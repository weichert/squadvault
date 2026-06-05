#!/usr/bin/env python3
"""sync_voice_from_supabase.py -- Supabase -> engine bridge for founding voice.

Reads a league's commissioner-approved founding Voice Profile from Supabase and
writes it into the engine's league_voice_profiles table, so a voice chosen in
the frontend founding session reaches recap generation.

This is the reverse of sync_to_supabase.py (which pushes APPROVED recaps up).
See _observations/OBSERVATIONS_2026_06_04_VOICE_BRIDGE_GAP.md for the gap this
closes and the design decisions (D1a-D6a).

DIRECTION:
  Supabase voice_profiles.prose  ->  engine league_voice_profiles.profile_text

GOVERNANCE PROPERTIES:
  - Read-only on Supabase; writes only league_voice_profiles on the engine.
  - Never touches recap_artifacts, approval state, or approval/audit events.
  - Authority gate (D4a): bridges only when leagues.first_approval_completed is
    true -- the commissioner has approved the founding outputs.
  - Payload (D1a): the frontend prose is authored as instruction-grade voice
    directive and is written verbatim as the engine profile_text. The register
    profile_key rides in approved_by for provenance; no schema change.
  - Idempotent: byte-identical profile_text is a no-op; safe to re-run.
  - Non-clobber (D5a): refuses to overwrite an engine row not authored by the
    bridge (approved_by not starting "founding-session") unless --force. This
    protects hand-curated profiles such as PFL Buddies'.
  - Engine-authoritative (D7b): leagues whose voice is curated engine-side
    (ENGINE_AUTHORITATIVE) are refused before any read, unless --force. PFL
    Buddies (70985) is demo-seeded on the frontend as falsely bridge-eligible;
    its real voice is engine-side, so it must not be bridged from the seed.
  - Skip / MIXED (D6a): a null voice_profile_id is a clean no-op; the engine's
    graceful default tone holds. A MIXED register chosen through the full
    founding flow has prose and bridges normally.
  - Writes one sync_log row to Supabase at end (skipped in --dry-run).
  - Per-league; fails clear with a specific message and a non-zero exit.

USAGE:
  ./scripts/py scripts/sync_voice_from_supabase.py --league-id 70985 --dry-run
  ./scripts/py scripts/sync_voice_from_supabase.py --league-id 70985
  ./scripts/py scripts/sync_voice_from_supabase.py --league-id 70985 --force
"""
from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from squadvault.core.storage.session import DatabaseSession
from squadvault.core.tone.voice_profile_v1 import set_voice_profile

from _env_bootstrap import bootstrap_env_local

logger = logging.getLogger("sync_voice_from_supabase")

DEFAULT_ENGINE_DB = Path(".local_squadvault.sqlite")
BRIDGE_AUTHOR_PREFIX = "founding-session"

# Leagues whose voice is authored and curated engine-side, not through the
# frontend founding session. The bridge refuses these before any read (unless
# --force): their frontend voice_profiles row is demo/seed data that would
# otherwise overwrite the curated engine voice. PFL Buddies (70985) is seeded
# on the frontend with first_approval_completed=true and placeholder prose,
# which makes it falsely look bridge-eligible. Remove an id here only if that
# league genuinely (re)founds its voice through the frontend.
ENGINE_AUTHORITATIVE = frozenset({"70985"})


# --- exit codes -------------------------------------------------------------

EXIT_OK = 0
EXIT_CONFIG = 2  # missing env / bad invocation
EXIT_NOT_FOUND = 3  # league not found in Supabase
EXIT_REFUSED = 4  # non-clobber guard tripped without --force
EXIT_UPSTREAM = 5  # Supabase read error


# --- pure decision core (no I/O; unit-testable without Supabase) ------------


def is_engine_authoritative(canonical_id: str) -> bool:
    """True if this league's voice is curated engine-side, not bridged."""
    return canonical_id in ENGINE_AUTHORITATIVE


@dataclass(frozen=True)
class BridgeDecision:
    action: str  # write | unchanged | skip_no_profile | skip_unapproved | refuse_clobber
    reason: str


def decide_bridge_action(
    *,
    voice_profile_id: str | None,
    first_approval_completed: bool,
    supabase_prose: str | None,
    engine_current_text: str | None,
    engine_current_approved_by: str | None,
    force: bool,
) -> BridgeDecision:
    """Decide what the bridge should do for one league. Pure; no side effects.

    Order of guards is deliberate: a missing selection (D6a) and an unapproved
    league (D4a) are normal no-ops checked before any prose comparison, so an
    empty or stale frontend row never reaches the write path.
    """
    if not voice_profile_id:
        return BridgeDecision(
            "skip_no_profile",
            "league has no voice_profile_id (skipped/MIXED-skip); engine default holds",
        )
    if not first_approval_completed:
        return BridgeDecision(
            "skip_unapproved",
            "founding outputs not yet approved (first_approval_completed is false)",
        )
    prose = (supabase_prose or "").strip()
    if not prose:
        return BridgeDecision(
            "skip_no_profile",
            "the pointed-at voice_profiles row has empty prose",
        )
    current = (engine_current_text or "").strip()
    if current == prose:
        return BridgeDecision("unchanged", "engine profile_text already byte-identical")
    if (
        current
        and engine_current_approved_by
        and not engine_current_approved_by.startswith(BRIDGE_AUTHOR_PREFIX)
        and not force
    ):
        return BridgeDecision(
            "refuse_clobber",
            "existing engine voice profile is not bridge-authored; pass --force to overwrite",
        )
    return BridgeDecision("write", "bridging approved founding voice to engine")


# --- engine-side read (direct; needs approved_by, which get_voice_profile omits) ---


def read_engine_voice_row(db_path: str, league_id: str) -> tuple[str | None, str | None]:
    """Return (profile_text, approved_by) for the engine row, or (None, None).

    Does not create the database file: a missing DB is treated as "no row", so
    a read never has a write side effect (D8a). Writes still create as needed.
    """
    import sqlite3 as _sqlite3

    if not Path(db_path).exists():
        return None, None
    try:
        with DatabaseSession(db_path) as con:
            row = con.execute(
                "SELECT profile_text, approved_by FROM league_voice_profiles WHERE league_id = ?",
                (league_id,),
            ).fetchone()
            if row:
                text = str(row[0]) if row[0] is not None else None
                by = str(row[1]) if row[1] is not None else None
                return text, by
    except (_sqlite3.OperationalError, _sqlite3.DatabaseError):
        logger.debug("read_engine_voice_row: failed to read engine row")
    return None, None


# --- Supabase-side read (lazy import; keeps module importable without the dep) ---


@dataclass(frozen=True)
class SupabaseVoice:
    league_uuid: str
    voice_profile_id: str | None
    first_approval_completed: bool
    prose: str | None
    profile_key: str | None


def _load_supabase_client():  # type: ignore[no-untyped-def]
    from supabase import create_client  # lazy: not needed for the decision core

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in env "
            "(via .env.local or the shell)."
        )
    return create_client(url, key)


def fetch_supabase_voice(client, canonical_id: str) -> SupabaseVoice | None:  # type: ignore[no-untyped-def]
    """Read the league and its pointed-at voice profile. Read-only."""
    league_resp = (
        client.table("leagues")
        .select("id, voice_profile_id, first_approval_completed")
        .eq("canonical_id", canonical_id)
        .limit(1)
        .execute()
    )
    rows = league_resp.data or []
    if not rows:
        return None
    league = rows[0]
    vp_id = league.get("voice_profile_id")
    prose: str | None = None
    profile_key: str | None = None
    if vp_id:
        vp_resp = (
            client.table("voice_profiles")
            .select("prose, profile_key")
            .eq("id", vp_id)
            .limit(1)
            .execute()
        )
        vp_rows = vp_resp.data or []
        if vp_rows:
            prose = vp_rows[0].get("prose")
            profile_key = vp_rows[0].get("profile_key")
    return SupabaseVoice(
        league_uuid=str(league["id"]),
        voice_profile_id=str(vp_id) if vp_id else None,
        first_approval_completed=bool(league.get("first_approval_completed")),
        prose=prose,
        profile_key=profile_key,
    )


# --- sync_log (mirrors sync_to_supabase.py's audit convention) --------------


def _git_hash() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _write_sync_log(client, *, status: str, action: str, canonical_id: str) -> None:  # type: ignore[no-untyped-def]
    counts = {
        "bridged": 1 if action == "write" else 0,
        "unchanged": 1 if action == "unchanged" else 0,
        "skipped": 1 if action in ("skip_no_profile", "skip_unapproved") else 0,
        "refused": 1 if action == "refuse_clobber" else 0,
    }
    client.table("sync_log").insert(
        {
            "engine_git_hash": _git_hash(),
            "tables_synced": {
                "direction": "supabase_to_engine",
                "target": "league_voice_profiles",
                "league": canonical_id,
            },
            "row_counts": counts,
            "status": status,
            "error_message": None,
        }
    ).execute()


# --- CLI --------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Bridge an approved founding Voice Profile from Supabase into the engine.",
    )
    p.add_argument("--league-id", required=True, help="Canonical league id, e.g. 70985.")
    p.add_argument("--db", default=str(DEFAULT_ENGINE_DB), help="Engine SQLite path.")
    p.add_argument("--dry-run", action="store_true", help="Report only; no engine write, no sync_log.")
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an engine row not authored by the bridge (D5a non-clobber override).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    bootstrap_env_local()
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    canonical_id = args.league_id

    if is_engine_authoritative(canonical_id) and not args.force:
        logger.error(
            "[%s] refused: this league's voice is engine-authoritative (curated "
            "engine-side); it is not bridged from the frontend, whose row for it "
            "is demo/seed data. Pass --force only to deliberately override.",
            canonical_id,
        )
        return EXIT_REFUSED

    try:
        client = _load_supabase_client()
    except RuntimeError as exc:
        logger.error("%s", exc)
        return EXIT_CONFIG

    try:
        sv = fetch_supabase_voice(client, canonical_id)
    except Exception as exc:  # noqa: BLE001 - report-and-exit, no partial writes
        logger.error("Supabase read failed: %s: %s", type(exc).__name__, exc)
        return EXIT_UPSTREAM

    if sv is None:
        logger.error("League %s not found in Supabase.", canonical_id)
        return EXIT_NOT_FOUND

    engine_text, engine_by = read_engine_voice_row(args.db, canonical_id)
    decision = decide_bridge_action(
        voice_profile_id=sv.voice_profile_id,
        first_approval_completed=sv.first_approval_completed,
        supabase_prose=sv.prose,
        engine_current_text=engine_text,
        engine_current_approved_by=engine_by,
        force=args.force,
    )

    logger.info("[%s] %s -> %s: %s", canonical_id, "decision", decision.action, decision.reason)

    if args.dry_run:
        logger.info("[%s] dry-run: no engine write, no sync_log row.", canonical_id)
        return EXIT_REFUSED if decision.action == "refuse_clobber" else EXIT_OK

    if decision.action == "refuse_clobber":
        _write_sync_log(client, status="refused", action=decision.action, canonical_id=canonical_id)
        return EXIT_REFUSED

    if decision.action == "write":
        assert sv.prose is not None
        approved_by = f"{BRIDGE_AUTHOR_PREFIX}:{sv.profile_key}" if sv.profile_key else BRIDGE_AUTHOR_PREFIX
        set_voice_profile(args.db, canonical_id, sv.prose, approved_by=approved_by)
        logger.info("[%s] wrote engine profile_text (approved_by=%s).", canonical_id, approved_by)

    _write_sync_log(client, status="success", action=decision.action, canonical_id=canonical_id)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
