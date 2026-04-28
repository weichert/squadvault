#!/usr/bin/env python3
"""Distribute one APPROVED weekly recap to the league channel.

This module is operational wiring on top of existing engine capabilities.
It does not mutate engine state. Distribution events live entirely in the
append-only archive frontmatter; the engine remains the canonical source
for what was *approved*, the archive is the canonical source for what was
*distributed*.

Default channel is ``group_text_paste_assist``: the script prepares the
league-facing message, writes a scratchpad to ``/tmp/``, prints the
message to stdout, and blocks on a confirmation prompt. Only after
confirmation does it write the archive entry — keeping ``human approves
publication`` literally inside the loop.

Distribution presupposes the artifact is in state ``APPROVED``. Approval
is governed by the Recap Review Heuristic, which is the binding judgment
about whether a recap is fit to publish. This script trusts that
judgment: it does not re-run verification, because re-running could
either be redundant (same result as approval time) or worse, surface a
post-approval verifier change as a contradiction with no resolution path.

Exit codes
----------
0   success (or successful dry run)
2   no artifact found for the requested week
3   most recent version is not in state APPROVED
4   APPROVED artifact has no extractable narrative
5   archive entry already exists (append-only invariant)
6   commissioner declined the confirmation prompt
130 commissioner aborted via Ctrl-C (POSIX SIGINT convention)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from squadvault.core.exports.season_html_export_v1 import extract_shareable_parts
from squadvault.core.storage.session import DatabaseSession

DEFAULT_LEAGUE_ID: Final[str] = "70985"
DEFAULT_ARCHIVE_ROOT: Final[str] = "archive/recaps"
DEFAULT_CHANNEL: Final[str] = "group_text_paste_assist"
SUPPORTED_CHANNELS: Final[frozenset[str]] = frozenset({DEFAULT_CHANNEL})

# Frontmatter key order is part of the contract: the archive is read by
# humans first and tools second, and the intentional grouping (identity →
# provenance → approval → distribution → companions) reads better than
# alphabetical.
_FRONTMATTER_KEY_ORDER: Final[tuple[str, ...]] = (
    "recap_artifact_id",
    "league_id",
    "season",
    "week_index",
    "artifact_type",
    "version",
    "state",
    "selection_fingerprint",
    "window_start",
    "window_end",
    "approved_by",
    "approved_at",
    "distributed_at",
    "distributed_to",
    "channel",
    "companion_files",
)


@dataclass(frozen=True)
class ApprovedArtifact:
    """Row shape for one weekly recap artifact, plus its rendered text."""

    recap_artifact_id: int
    league_id: str
    season: int
    week_index: int
    artifact_type: str
    version: int
    state: str
    selection_fingerprint: str
    window_start: str | None
    window_end: str | None
    approved_by: str | None
    approved_at: str | None
    rendered_text: str


@dataclass(frozen=True)
class ArchivePaths:
    """Filesystem destinations for one archived distribution."""

    md_path: Path
    json_path: Path


# ---------------------------------------------------------------------------
# DB access (read-only)
# ---------------------------------------------------------------------------


def _load_latest_artifact(
    con: sqlite3.Connection,
    *,
    league_id: str,
    season: int,
    week_index: int,
) -> ApprovedArtifact | None:
    """Return the highest-version weekly recap row, regardless of state.

    State filtering happens in Python rather than SQL so the caller can
    write a precise refusal message naming what was actually found.
    """
    row = con.execute(
        """
        SELECT id, league_id, season, week_index, artifact_type, version, state,
               selection_fingerprint, window_start, window_end,
               approved_by, approved_at, rendered_text
          FROM recap_artifacts
         WHERE league_id = ?
           AND season = ?
           AND week_index = ?
           AND artifact_type = 'WEEKLY_RECAP'
         ORDER BY version DESC
         LIMIT 1
        """,
        (league_id, season, week_index),
    ).fetchone()

    if row is None:
        return None

    return ApprovedArtifact(
        recap_artifact_id=row[0],
        league_id=row[1],
        season=row[2],
        week_index=row[3],
        artifact_type=row[4],
        version=row[5],
        state=row[6],
        selection_fingerprint=row[7],
        window_start=row[8],
        window_end=row[9],
        approved_by=row[10],
        approved_at=row[11],
        rendered_text=row[12] or "",
    )


# ---------------------------------------------------------------------------
# League-facing message formatting
# ---------------------------------------------------------------------------


def _format_for_paste_assist(
    *,
    narrative: str,
    bullets: list[str],
    season: int,
    week_index: int,
) -> str:
    """Compose the message body the commissioner pastes into the thread.

    Format is intentionally minimal: header, narrative, optional bullets
    section. No state line, no telemetry, no metadata — those live in the
    archive, not in what the league reads.
    """
    header = f"PFL Buddies — Season {season}, Week {week_index}"
    parts: list[str] = [header, "=" * len(header), "", narrative]
    if bullets:
        parts.extend(["", "---", "", "What happened this week:"])
        parts.extend(f"- {item}" for item in bullets)
    return "\n".join(parts).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Archive writing (append-only)
# ---------------------------------------------------------------------------


def _archive_paths(
    archive_root: Path,
    *,
    season: int,
    week_index: int,
    version: int,
) -> ArchivePaths:
    season_dir = archive_root / str(season)
    base = f"week_{week_index:02d}__v{version}"
    return ArchivePaths(
        md_path=season_dir / f"{base}.md",
        json_path=season_dir / f"{base}.json",
    )


def _yaml_scalar(value: object) -> str:
    """Render one scalar for YAML frontmatter.

    Strings are double-quoted with backslash and double-quote escaped.
    Integers are emitted bare. ``None`` becomes ``null``. Booleans are
    not used in this schema but are handled defensively.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _render_frontmatter(meta: dict[str, object]) -> str:
    """Emit YAML frontmatter using the contracted key order.

    A focused emitter rather than a YAML library: the schema is fixed,
    values are simple, and intentional ordering is part of the contract.
    """
    lines: list[str] = ["---"]
    for key in _FRONTMATTER_KEY_ORDER:
        if key not in meta:
            continue
        value = meta[key]
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key in sorted(value):
                lines.append(f"  {sub_key}: {_yaml_scalar(value[sub_key])}")
        else:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _write_archive(
    paths: ArchivePaths,
    *,
    artifact: ApprovedArtifact,
    message: str,
    distributed_at: str,
    distributed_to: str,
    channel: str,
) -> None:
    """Write the .md (frontmatter + body) and .json (audit companion).

    Refuses to overwrite either file. Ensures the parent directory
    exists. Append-only is enforced both here (filesystem-level) and at
    the call site (early refusal with explicit message).
    """
    if paths.md_path.exists():
        raise FileExistsError(
            f"Archive entry already exists: {paths.md_path}. "
            f"The append-only invariant forbids overwriting."
        )
    if paths.json_path.exists():
        raise FileExistsError(
            f"Archive companion already exists: {paths.json_path}."
        )

    paths.md_path.parent.mkdir(parents=True, exist_ok=True)

    frontmatter_meta: dict[str, object] = {
        "recap_artifact_id": artifact.recap_artifact_id,
        "league_id": artifact.league_id,
        "season": artifact.season,
        "week_index": artifact.week_index,
        "artifact_type": artifact.artifact_type,
        "version": artifact.version,
        "state": artifact.state,
        "selection_fingerprint": artifact.selection_fingerprint,
        "window_start": artifact.window_start,
        "window_end": artifact.window_end,
        "approved_by": artifact.approved_by,
        "approved_at": artifact.approved_at,
        "distributed_at": distributed_at,
        "distributed_to": distributed_to,
        "channel": channel,
        "companion_files": {"recap_json": paths.json_path.name},
    }

    paths.md_path.write_text(
        _render_frontmatter(frontmatter_meta) + "\n" + message,
        encoding="utf-8",
    )

    audit_payload: dict[str, object] = dict(frontmatter_meta)
    audit_payload["rendered_text"] = artifact.rendered_text
    paths.json_path.write_text(
        json.dumps(audit_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Orchestration helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    """ISO-8601 UTC timestamp matching the engine's storage convention."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _scratchpad_path(*, season: int, week_index: int) -> Path:
    return Path(f"/tmp/distribute_{season}_w{week_index:02d}.txt")


def _confirm_pasted_interactive() -> bool:
    """Block on commissioner confirmation that the paste happened.

    Stderr carries the prompt; stdin carries the response. Returns
    ``True`` on confirmation, ``False`` on graceful refusal. Ctrl-C is
    raised as KeyboardInterrupt for the caller to handle distinctly.
    """
    sys.stderr.write(
        "\nPaste the message above into the PFL Buddies group thread.\n"
        "Press Enter to confirm distribution and write the archive,\n"
        "or type 'no' (and Enter) to abort without archiving: "
    )
    sys.stderr.flush()
    response = input().strip().lower()
    return response in ("", "y", "yes")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Distribute one APPROVED weekly recap to the league channel and "
            "record the distribution in the append-only archive."
        ),
    )
    parser.add_argument("--db", required=True, help="Path to engine SQLite DB.")
    parser.add_argument("--league-id", default=DEFAULT_LEAGUE_ID)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--week-index", type=int, required=True)
    parser.add_argument(
        "--channel",
        default=DEFAULT_CHANNEL,
        choices=sorted(SUPPORTED_CHANNELS),
        help="Distribution channel handler.",
    )
    parser.add_argument(
        "--archive-root",
        default=DEFAULT_ARCHIVE_ROOT,
        help="Root directory for the distribution archive.",
    )
    parser.add_argument(
        "--distributed-to",
        default="league_channel",
        help="Recipient label recorded in archive frontmatter.",
    )
    parser.add_argument(
        "--confirm-pasted",
        action="store_true",
        help="Skip the interactive prompt; assume the paste happened.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and write the scratchpad only; do not prompt or archive.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    archive_root = Path(args.archive_root).resolve()

    with DatabaseSession(args.db) as con:
        artifact = _load_latest_artifact(
            con,
            league_id=args.league_id,
            season=args.season,
            week_index=args.week_index,
        )

    if artifact is None:
        sys.stderr.write(
            f"No WEEKLY_RECAP artifact found for "
            f"(league_id={args.league_id}, season={args.season}, "
            f"week_index={args.week_index}).\n"
        )
        return 2

    if artifact.state != "APPROVED":
        sys.stderr.write(
            f"Refusing to distribute: most recent artifact for "
            f"(season={artifact.season}, week={artifact.week_index}) "
            f"is version {artifact.version} in state {artifact.state}, "
            f"not APPROVED.\n"
            f"Distribution requires APPROVED state. Approval is governed by "
            f"the Recap Review Heuristic.\n"
        )
        return 3

    narrative, bullets = extract_shareable_parts(artifact.rendered_text)
    if not narrative:
        sys.stderr.write(
            f"Refusing to distribute: APPROVED artifact "
            f"(id={artifact.recap_artifact_id}) has no extractable narrative "
            f"in rendered_text.\n"
        )
        return 4

    paths = _archive_paths(
        archive_root,
        season=artifact.season,
        week_index=artifact.week_index,
        version=artifact.version,
    )
    if paths.md_path.exists() or paths.json_path.exists():
        sys.stderr.write(
            f"Refusing to distribute: archive entry already exists at "
            f"{paths.md_path}.\n"
            f"This artifact (season={artifact.season}, "
            f"week={artifact.week_index}, version={artifact.version}) "
            f"has already been distributed.\n"
            f"The archive is append-only; the existing file is canonical.\n"
        )
        return 5

    message = _format_for_paste_assist(
        narrative=narrative,
        bullets=bullets,
        season=artifact.season,
        week_index=artifact.week_index,
    )

    scratchpad = _scratchpad_path(
        season=artifact.season, week_index=artifact.week_index
    )
    scratchpad.write_text(message, encoding="utf-8")
    sys.stdout.write(message)
    sys.stdout.write(f"\n[scratchpad: {scratchpad}]\n")
    sys.stdout.flush()

    if args.dry_run:
        sys.stderr.write("Dry run: no prompt, no archive.\n")
        return 0

    if not args.confirm_pasted:
        try:
            confirmed = _confirm_pasted_interactive()
        except KeyboardInterrupt:
            sys.stderr.write("\nAborted: no archive written.\n")
            return 130
        if not confirmed:
            sys.stderr.write("Aborted: no archive written.\n")
            return 6

    _write_archive(
        paths,
        artifact=artifact,
        message=message,
        distributed_at=_utc_now_iso(),
        distributed_to=args.distributed_to,
        channel=args.channel,
    )

    sys.stderr.write(
        f"\nArchive written:\n  {paths.md_path}\n  {paths.json_path}\n"
        f"\nNext step:\n"
        f"  git add archive/recaps/\n"
        f'  git commit -m "archive: distribute season {artifact.season} '
        f'week {artifact.week_index} v{artifact.version}"\n'
        f"  git push origin main\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
