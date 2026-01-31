from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

from squadvault.consumers.editorial_actions import insert_editorial_action


def latest_version_and_state(
    conn: sqlite3.Connection, league_id: str, season: int, week_index: int
) -> tuple[int | None, str | None]:
    cur = conn.execute(
        """
        SELECT version, state
        FROM recap_artifacts
        WHERE league_id=? AND season=? AND week_index=?
        ORDER BY version DESC
        LIMIT 1;
        """,
        (league_id, int(season), int(week_index)),
    )
    row = cur.fetchone()
    if not row:
        return None, None
    return int(row[0]), str(row[1])


def die(msg: str, code: int = 2) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return code


def recap_dir(base_dir: str, league_id: str, season: int, week_index: int) -> Path:
    return Path(base_dir) / "recaps" / str(league_id) / str(season) / f"week_{int(week_index):02d}"


_V_RE = re.compile(r"recap_v(\d+)\.json$")


def find_latest_recap_json(base_dir: str, league_id: str, season: int, week_index: int) -> Optional[Path]:
    d = recap_dir(base_dir, league_id, season, week_index)
    if not d.exists():
        return None
    candidates = []
    for p in sorted(d.glob("recap_v*.json")):
        m = _V_RE.search(p.name)
        if not m:
            continue
        candidates.append((int(m.group(1)), p))
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[-1][1]


def parse_recap_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_version(path: Path, payload: dict) -> int:
    # Prefer explicit field if present
    for k in ("version", "artifact_version", "recap_version"):
        if k in payload and isinstance(payload[k], int):
            return int(payload[k])
    # Fallback to filename
    m = _V_RE.search(path.name)
    if not m:
        raise ValueError(f"Cannot infer version from {path}")
    return int(m.group(1))


def extract_fingerprint(payload: dict) -> Optional[str]:
    # We’ve seen selection fingerprints in run metadata; try common keys
    for k in ("selection_fingerprint", "fingerprint", "selectionFingerprint"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # Sometimes nested in metadata
    meta = payload.get("metadata")
    if isinstance(meta, dict):
        v = meta.get("selection_fingerprint") or meta.get("fingerprint")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def render_review_packet(
    db: str,
    league_id: str,
    season: int,
    week_index: int,
    version: int | None,
    *,
    voices: list[str] | None,
    base_dir: str,
) -> str:
    """Render a commissioner review packet using the existing renderer.

    Creative Layer stays strictly downstream:
    - no schema changes
    - no DB writes
    - voice variants are render-time only
    """
    py = "src/squadvault/consumers/recap_week_render.py"
    cmd = [
        sys.executable,
        "-u",
        py,
        "--db",
        db,
        "--league-id",
        league_id,
        "--season",
        str(season),
        "--week-index",
        str(week_index),
        "--base-dir",
        base_dir,
        "--suppress-render-warning",
    ]
    if version is not None:
        cmd += ["--version", str(version)]

    if voices:
        for v in voices:
            cmd += ["--voice", v]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        raise RuntimeError(f"Renderer failed (rc={proc.returncode}). stderr:\n{err}")
    if not out:
        return err or "(renderer produced no output)"
    return out


def run_script(py_path: str, args: list[str]) -> int:
    cmd = [sys.executable, "-u", py_path] + args
    return subprocess.call(cmd)


def ensure_draft_exists(
    db: str, league_id: str, season: int, week_index: int, base_dir: str
) -> Tuple[Path, dict]:
    latest = find_latest_recap_json(base_dir, league_id, season, week_index)
    if latest is None:
        # Create draft artifact on disk (existing consumer)
        py = "src/squadvault/consumers/recap_week_write_artifact.py"
        rc = run_script(
            py,
            [
                "--db",
                db,
                "--league-id",
                league_id,
                "--season",
                str(season),
                "--week-index",
                str(week_index),
                "--base-dir",
                base_dir,
            ],
        )
        if rc != 0:
            raise RuntimeError(f"Failed to create draft via {py} (rc={rc})")
        latest = find_latest_recap_json(base_dir, league_id, season, week_index)
        if latest is None:
            raise RuntimeError("Draft still not found after write_artifact")
    payload = parse_recap_json(latest)
    return latest, payload


def prompt(prompt_text: str) -> str:
    try:
        return input(prompt_text)
    except EOFError:
        return ""


def review_loop(
    db: str,
    league_id: str,
    season: int,
    week_index: int,
    actor: str,
    base_dir: str,
    voices: list[str],
) -> int:
    conn = sqlite3.connect(db)

    latest_v, state = latest_version_and_state(conn, league_id, season, week_index)

    # Best-effort disk lookup (may be stale/absent for APPROVED weeks)
    recap_path, payload = ensure_draft_exists(db, league_id, season, week_index, base_dir)
    version = latest_v if latest_v is not None else extract_version(recap_path, payload)
    fp = extract_fingerprint(payload)

    insert_editorial_action(
        conn,
        league_id=league_id,
        season=season,
        week_index=week_index,
        artifact_kind="WEEKLY_RECAP",
        artifact_version=version,
        selection_fingerprint=fp,
        action="OPEN",
        actor=actor,
        notes_md=None,
    )

    rendered = render_review_packet(
        db,
        league_id,
        season,
        week_index,
        version,
        voices=voices,
        base_dir=base_dir,
    )

    print("")
    print("============================================================")
    print(f"Commissioner Review — League {league_id} — Season {season} — Week {week_index}")
    print(f"Artifact file (best-effort): {recap_path}")
    print(f"Version: v{version:02d}" + (f"  (state: {state})" if state else ""))
    print("============================================================")
    print("")
    print("=== REVIEW PACKET (renderer output) ===")
    print(rendered)
    print("")

    print("Decision:")
    if state == "APPROVED":
        print("  [R] Regenerate (creates new draft version)")
        print("  [N] Notes-only (no state change)")
        print("  [Q] Quit")
    else:
        print("  [A] Approve")
        print("  [R] Regenerate (creates new draft version)")
        print("  [W] Withhold")
        print("  [N] Notes-only (no state change)")
        print("  [Q] Quit")

    choice = prompt("Choose " + ("R/N/Q" if state == "APPROVED" else "A/R/W/N/Q") + ": ").strip().upper()

    if choice in ("Q", ""):
        print("Exiting without decision.")
        return 0

    notes = prompt("Optional notes (single line; leave blank for none): ").rstrip()
    notes_md = notes if notes.strip() else None

    if choice == "N":
        insert_editorial_action(
            conn,
            league_id=league_id,
            season=season,
            week_index=week_index,
            artifact_kind="WEEKLY_RECAP",
            artifact_version=version,
            selection_fingerprint=fp,
            action="NOTES",
            actor=actor,
            notes_md=notes_md,
        )
        print("Notes recorded.")
        return 0

    if choice == "A":
        if state == "APPROVED":
            print("Already APPROVED. Use Regenerate to create a new draft version for changes.")
            return 0
        insert_editorial_action(
            conn,
            league_id=league_id,
            season=season,
            week_index=week_index,
            artifact_kind="WEEKLY_RECAP",
            artifact_version=version,
            selection_fingerprint=fp,
            action="APPROVE",
            actor=actor,
            notes_md=notes_md,
        )
        py = "src/squadvault/consumers/recap_artifact_approve.py"
        rc = run_script(
            py,
            [
                "--db",
                db,
                "--league-id",
                league_id,
                "--season",
                str(season),
                "--week-index",
                str(week_index),
                "--version",
                str(version),
                "--approved-by",
                actor,
            ],
        )
        return rc

    if choice == "W":
        if state == "APPROVED":
            print("This week is already APPROVED. Use Regenerate to create a new draft version first.")
            return 1
        insert_editorial_action(
            conn,
            league_id=league_id,
            season=season,
            week_index=week_index,
            artifact_kind="WEEKLY_RECAP",
            artifact_version=version,
            selection_fingerprint=fp,
            action="WITHHOLD",
            actor=actor,
            notes_md=notes_md,
        )
        py = "src/squadvault/consumers/recap_artifact_withhold.py"
        rc = run_script(
            py,
            [
                "--db",
                db,
                "--league-id",
                league_id,
                "--season",
                str(season),
                "--week-index",
                str(week_index),
                "--withheld-by",
                actor,
                "--reason",
                "EDITORIAL_WITHHOLD",
            ],
        )
        return rc

    if choice == "R":
        insert_editorial_action(
            conn,
            league_id=league_id,
            season=season,
            week_index=week_index,
            artifact_kind="WEEKLY_RECAP",
            artifact_version=version,
            selection_fingerprint=fp,
            action="REGENERATE",
            actor=actor,
            notes_md=notes_md,
        )

        py = "src/squadvault/consumers/recap_artifact_regenerate.py"
        regen_args = [
            "--db",
            db,
            "--league-id",
            league_id,
            "--season",
            str(season),
            "--week-index",
            str(week_index),
            "--reason",
            "EDITORIAL_REGENERATE",
            "--created-by",
            actor,
        ]
        if state == "APPROVED":
            regen_args.append("--force")

        rc = run_script(py, regen_args)
        if rc != 0:
            return rc

        # Explicit loop: reopen review on the newest draft
        return review_loop(db, league_id, season, week_index, actor, base_dir, voices)

    return die(f"Unknown choice: {choice}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Commissioner editorial review loop (Phase 1)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--week-index", type=int, required=True)
    ap.add_argument("--actor", required=True)
    ap.add_argument("--base-dir", default="artifacts", help="Artifact base dir (default: artifacts)")

    # Phase 2.1: voice pack for review (repeatable)
    ap.add_argument(
        "--voice",
        action="append",
        default=[],
        help="Render non-canonical voice variant (repeatable). If omitted, defaults to neutral/playful/dry.",
    )

    args = ap.parse_args(argv)

    voices = args.voice if args.voice else ["neutral", "playful", "dry"]

    return review_loop(
        db=args.db,
        league_id=args.league_id,
        season=args.season,
        week_index=args.week_index,
        actor=args.actor,
        base_dir=args.base_dir,
        voices=voices,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
