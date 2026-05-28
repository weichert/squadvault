#!/usr/bin/env python3
"""sync_to_supabase.py — Engine -> Supabase bridge for APPROVED artifacts.

Reads APPROVED rows from .local_squadvault.sqlite recap_artifacts and pushes
them to Supabase staging as (artifacts, artifact_versions, docket_ids) rows.

SCOPE (Milestone 3, Phase 11):
  - E1 (WEEKLY_RECAP)              — included
  - F1 (RIVALRY_CHRONICLE_V1)      — included if any APPROVED rows exist
  - A1/A2/A3                        — NOT INCLUDED
        These are filesystem-only artifacts (archive/<surface>/*.md) whose
        governance event is the git commit of the archive directory. They
        do not live in recap_artifacts and require a separate
        filesystem-source spec. Deferred to a follow-on milestone.

GOVERNANCE PROPERTIES:
  - Read-only on engine DB
  - Idempotent by (engine_artifact_id); new versions detected by hash mismatch
  - Never modifies Supabase approval_state post-insert
  - Never writes approval_events (sync is backfill of externally-governed
    state; no actor_user_id available, and the audit trail belongs to the
    engine side)
  - Writes one sync_log row at end of run (skipped in --dry-run)
  - Fails per-artifact on error; batch continues with that row rolled back

USAGE:
  ./scripts/py scripts/sync_to_supabase.py --dry-run
  ./scripts/py scripts/sync_to_supabase.py --type WEEKLY_RECAP --season 2025
  ./scripts/py scripts/sync_to_supabase.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sqlite3
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Third-party (engine repo: add to requirements if not present)
#   pip install supabase
from supabase import Client, create_client

# ─── Constants ───────────────────────────────────────────────────────────────

DEFAULT_ENGINE_DB = Path(".local_squadvault.sqlite")
DEFAULT_LEAGUE_CANONICAL_ID = "70985"

# CERTIFIED trust bar (middle dot, not pipe — Design Brief §8)
TRUST_BAR_CERTIFIED = "Entered into the Record \u00b7 Source Facts Verified \u00b7 SquadVault"

# Engine artifact types syncable by this script
ENGINE_ARTIFACT_TYPE_WEEKLY_RECAP = "WEEKLY_RECAP"
ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1 = "RIVALRY_CHRONICLE_V1"

SYNCABLE_ENGINE_TYPES = (
    ENGINE_ARTIFACT_TYPE_WEEKLY_RECAP,
    ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1,
)

# Engine -> Supabase artifact_type / artifact_class mapping
# (Supabase CHECK constraint rejects '_V1' suffix on artifact_type.)
TYPE_MAPPING: dict[str, tuple[str, str]] = {
    ENGINE_ARTIFACT_TYPE_WEEKLY_RECAP:        ("WEEKLY_RECAP",      "E1"),
    ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1: ("RIVALRY_CHRONICLE", "F1"),
}

# ─── Logging ─────────────────────────────────────────────────────────────────

log = logging.getLogger("sync_to_supabase")


def _configure_logging(verbose: bool, log_file: Path | None) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s %(levelname)-7s %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


# ─── Engine read model ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class EngineArtifact:
    """A single APPROVED row from recap_artifacts (engine side)."""

    id: int
    league_id: str
    season: int
    week_index: int
    artifact_type: str
    version: int
    selection_fingerprint: str
    window_start: str | None
    window_end: str | None
    rendered_text: str
    approved_at: str | None
    created_at: str

    @property
    def supabase_artifact_type(self) -> str:
        return TYPE_MAPPING[self.artifact_type][0]

    @property
    def artifact_class(self) -> str:
        return TYPE_MAPPING[self.artifact_type][1]

    @property
    def docket_id(self) -> str:
        """Deterministic docket constructed from engine identity.

        E1: SV-{SEASON}-W{WEEK:02d}-V{VERSION:02d}            e.g. SV-2025-W07-V27
        F1: SV-{SEASON}-W{WEEK:02d}-CHRONICLE-V{VERSION:02d}  e.g. SV-2025-W12-CHRONICLE-V03
        """
        if self.artifact_type == ENGINE_ARTIFACT_TYPE_WEEKLY_RECAP:
            return f"SV-{self.season}-W{self.week_index:02d}-V{self.version:02d}"
        if self.artifact_type == ENGINE_ARTIFACT_TYPE_RIVALRY_CHRONICLE_V1:
            return (
                f"SV-{self.season}-W{self.week_index:02d}"
                f"-CHRONICLE-V{self.version:02d}"
            )
        raise ValueError(f"Unsupported engine artifact_type for docket: {self.artifact_type}")

    @property
    def source_hash(self) -> str:
        """SHA-256 of rendered_text — identity key for new-version detection."""
        return hashlib.sha256(self.rendered_text.encode("utf-8")).hexdigest()


def _load_engine_artifacts(
    db_path: Path,
    *,
    types: tuple[str, ...],
    season: int | None,
) -> Iterator[EngineArtifact]:
    """Stream APPROVED engine artifacts. Warns on any APPROVED-with-NULL rendered_text."""
    if not db_path.exists():
        raise FileNotFoundError(f"Engine DB not found: {db_path}")

    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        con.row_factory = sqlite3.Row

        # Anomaly probe: count APPROVED rows with NULL rendered_text
        anomaly = con.execute(
            "SELECT COUNT(*) FROM recap_artifacts "
            "WHERE state='APPROVED' AND rendered_text IS NULL",
        ).fetchone()[0]
        if anomaly:
            log.warning(
                "Engine has %d APPROVED row(s) with NULL rendered_text "
                "— skipping; investigate post-sync.",
                anomaly,
            )

        placeholders = ",".join("?" for _ in types)
        params: list[object] = list(types)
        season_clause = ""
        if season is not None:
            season_clause = " AND season=?"
            params.append(int(season))

        sql = (
            "SELECT id, league_id, season, week_index, artifact_type, version, "
            "       selection_fingerprint, window_start, window_end, "
            "       rendered_text, approved_at, created_at "
            "FROM recap_artifacts "
            f"WHERE state='APPROVED' AND rendered_text IS NOT NULL "
            f"  AND artifact_type IN ({placeholders})"
            f"{season_clause} "
            "ORDER BY season, week_index, artifact_type, version"
        )

        for row in con.execute(sql, params):
            yield EngineArtifact(
                id=int(row["id"]),
                league_id=str(row["league_id"]),
                season=int(row["season"]),
                week_index=int(row["week_index"]),
                artifact_type=str(row["artifact_type"]),
                version=int(row["version"]),
                selection_fingerprint=str(row["selection_fingerprint"]),
                window_start=row["window_start"],
                window_end=row["window_end"],
                rendered_text=str(row["rendered_text"]),
                approved_at=row["approved_at"],
                created_at=str(row["created_at"]),
            )
    finally:
        con.close()


# ─── Supabase write model ────────────────────────────────────────────────────

def _resolve_league_uuid(client: Client, canonical_id: str) -> str:
    resp = (
        client.table("leagues")
        .select("id")
        .eq("canonical_id", canonical_id)
        .single()
        .execute()
    )
    if not resp.data or "id" not in resp.data:
        raise RuntimeError(
            f"League with canonical_id={canonical_id!r} not found in Supabase. "
            f"Seed it before running sync.",
        )
    return str(resp.data["id"])


def _find_existing_artifact(
    client: Client, engine_artifact_id: int
) -> dict | None:
    resp = (
        client.table("artifacts")
        .select("id, current_version, engine_source_hash, approval_state, docket_id")
        .eq("engine_artifact_id", str(engine_artifact_id))
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def _insert_new_artifact(
    client: Client,
    *,
    league_uuid: str,
    engine: EngineArtifact,
    source_hash: str,
) -> str:
    """Insert artifacts row + artifact_versions v1 + docket_ids row. Returns artifact uuid."""
    sb_type, sb_class = engine.supabase_artifact_type, engine.artifact_class

    artifact_resp = (
        client.table("artifacts")
        .insert(
            {
                "league_id":          league_uuid,
                "artifact_type":      sb_type,
                "artifact_class":     sb_class,
                "season":             engine.season,
                "week_index":         engine.week_index,
                "engine_artifact_id": str(engine.id),
                "engine_source_hash": source_hash,
                "approval_state":     "APPROVED",   # bypasses BEFORE UPDATE trigger
                "current_version":    1,
                "is_demo":            False,
                "docket_id":          engine.docket_id,
                "trust_bar_text":     TRUST_BAR_CERTIFIED,
                "approved_at":        engine.approved_at,
            }
        )
        .execute()
    )
    if not artifact_resp.data:
        raise RuntimeError(f"Insert artifacts returned no row for engine id={engine.id}")
    artifact_uuid = str(artifact_resp.data[0]["id"])

    client.table("artifact_versions").insert(
        {
            "artifact_id":      artifact_uuid,
            "version":          1,
            "content_markdown": engine.rendered_text,
            "generated_by":     "engine",
        }
    ).execute()

    client.table("docket_ids").insert(
        {
            "artifact_id":     artifact_uuid,
            "docket_value":    engine.docket_id,
            "year":            engine.season,
            "sequence_number": engine.version,  # engine version, deterministic & re-derivable
            "is_demo":         False,
        }
    ).execute()

    return artifact_uuid


def _append_new_version(
    client: Client,
    *,
    existing: dict,
    engine: EngineArtifact,
    source_hash: str,
) -> int:
    """Insert next artifact_versions row, bump current_version on artifacts. Returns new version number."""
    artifact_uuid = str(existing["id"])
    new_version = int(existing["current_version"]) + 1

    client.table("artifact_versions").insert(
        {
            "artifact_id":      artifact_uuid,
            "version":          new_version,
            "content_markdown": engine.rendered_text,
            "generated_by":     "engine",
        }
    ).execute()

    # current_version + engine_source_hash bump only — does not touch approval_state,
    # so the state-transition trigger does not fire.
    client.table("artifacts").update(
        {
            "current_version":    new_version,
            "engine_source_hash": source_hash,
        }
    ).eq("id", artifact_uuid).execute()

    return new_version


# ─── Sync orchestration ──────────────────────────────────────────────────────

@dataclass
class RunCounts:
    inserted: int = 0
    versioned: int = 0
    skipped: int = 0
    failed: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "inserted":  self.inserted,
            "versioned": self.versioned,
            "skipped":   self.skipped,
            "failed":    self.failed,
        }


def _sync_one(
    client: Client | None,
    league_uuid: str,
    engine: EngineArtifact,
    *,
    dry_run: bool,
    counts: RunCounts,
) -> None:
    src_hash = engine.source_hash
    tag = f"id={engine.id} {engine.artifact_type} {engine.season}W{engine.week_index:02d}v{engine.version}"

    try:
        if dry_run:
            log.info("[DRY] WOULD-INSERT %s  docket=%s hash=%s",
                     tag, engine.docket_id, src_hash[:12])
            counts.inserted += 1
            return

        assert client is not None
        existing = _find_existing_artifact(client, engine.id)

        if existing is None:
            uuid = _insert_new_artifact(
                client,
                league_uuid=league_uuid,
                engine=engine,
                source_hash=src_hash,
            )
            log.info("INSERT %s  -> artifact=%s docket=%s", tag, uuid, engine.docket_id)
            counts.inserted += 1
            return

        if existing.get("engine_source_hash") == src_hash:
            log.info("SKIP   %s  (hash unchanged)", tag)
            counts.skipped += 1
            return

        new_v = _append_new_version(
            client,
            existing=existing,
            engine=engine,
            source_hash=src_hash,
        )
        log.info("VERSION %s -> v%d on artifact=%s", tag, new_v, existing["id"])
        counts.versioned += 1

    except Exception as exc:  # per-artifact roll back, batch continues
        counts.failed += 1
        log.error("FAILED %s — %s: %s", tag, type(exc).__name__, exc)


def _engine_git_hash() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _write_sync_log(
    client: Client,
    *,
    status: str,
    counts: RunCounts,
    types_synced: tuple[str, ...],
    git_hash: str | None,
    error: str | None,
) -> None:
    client.table("sync_log").insert(
        {
            "engine_git_hash": git_hash,
            "tables_synced":   {"engine_types": list(types_synced)},
            "row_counts":      counts.as_dict(),
            "status":          status,
            "error_message":   error,
        }
    ).execute()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Sync APPROVED engine artifacts to Supabase staging.",
    )
    p.add_argument("--dry-run", action="store_true",
                   help="Read and plan; do not write to Supabase.")
    p.add_argument("--type", choices=SYNCABLE_ENGINE_TYPES, default=None,
                   help="Restrict to a single engine artifact_type.")
    p.add_argument("--season", type=int, default=None,
                   help="Restrict to a single season.")
    p.add_argument("--db", type=Path, default=DEFAULT_ENGINE_DB,
                   help=f"Engine SQLite path (default: {DEFAULT_ENGINE_DB}).")
    p.add_argument("--league-canonical-id", default=DEFAULT_LEAGUE_CANONICAL_ID,
                   help="MFL canonical league id (default: PFL Buddies / 70985).")
    p.add_argument("--limit", type=int, default=None,
                   help="Cap rows processed (for smoke tests).")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="DEBUG-level logging.")
    return p.parse_args(argv)


def _build_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in env "
            "(propagate .env.local with `set -a; source .env.local; set +a`).",
        )
    return create_client(url, key)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    log_file = Path("logs") / f"sync_to_supabase_{today}.log"
    _configure_logging(args.verbose, log_file=None if args.dry_run else log_file)

    types = (args.type,) if args.type else SYNCABLE_ENGINE_TYPES
    git_hash = _engine_git_hash()

    log.info("─" * 60)
    log.info("sync_to_supabase  dry_run=%s  types=%s  season=%s  db=%s",
             args.dry_run, types, args.season, args.db)
    log.info("engine git HEAD: %s", git_hash or "(unknown)")

    client: Client | None = None
    league_uuid = "<dry-run>"
    if not args.dry_run:
        client = _build_client()
        league_uuid = _resolve_league_uuid(client, args.league_canonical_id)
        log.info("Supabase league_id resolved: %s -> %s",
                 args.league_canonical_id, league_uuid)

    counts = RunCounts()
    run_status = "success"
    run_error: str | None = None

    try:
        processed = 0
        for engine in _load_engine_artifacts(args.db, types=types, season=args.season):
            if args.limit is not None and processed >= args.limit:
                log.info("--limit %d reached; stopping early.", args.limit)
                break
            _sync_one(client, league_uuid, engine, dry_run=args.dry_run, counts=counts)
            processed += 1
    except Exception as exc:  # batch-level failure (e.g. DB open)
        run_status = "error"
        run_error = f"{type(exc).__name__}: {exc}"
        log.exception("Batch aborted: %s", run_error)

    log.info("Counts: %s", json.dumps(counts.as_dict()))

    if not args.dry_run and client is not None:
        try:
            _write_sync_log(
                client,
                status=run_status if counts.failed == 0 else "partial",
                counts=counts,
                types_synced=types,
                git_hash=git_hash,
                error=run_error,
            )
        except Exception as exc:
            log.error("Failed to write sync_log row: %s: %s", type(exc).__name__, exc)

    return 0 if (run_status == "success" and counts.failed == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
