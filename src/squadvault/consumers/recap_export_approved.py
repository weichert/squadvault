from __future__ import annotations

import json

import argparse
from pathlib import Path

from squadvault.core.exports.approved_weekly_recap_export_v1 import (
    fetch_latest_approved_weekly_recap,
    write_approved_weekly_recap_export_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Export latest APPROVED weekly recap artifact to a portable bundle."
    )
    p.add_argument("--db", required=True)
    p.add_argument("--league-id", required=True)
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--week-index", type=int, required=True)

    # Either out-dir OR out-root
    p.add_argument("--out-dir", help="Exact directory to write export bundle into.")
    p.add_argument(
        "--out-root",
        help="Root directory under which canonical path will be created "
             "(league/season/week_xx/approved_vN).",
    )

    p.add_argument("--version", type=int, default=None, help="Optional: export a specific APPROVED version.")
    p.add_argument(
        "--non-deterministic",
        action="store_true",
        help="Include volatile metadata like exported_at (default is deterministic).",
    )
    return p


def _canonical_out_dir(
    out_root: Path,
    league_id: str,
    season: int,
    week_index: int,
    version: int,
) -> Path:
    return (
        out_root
        / str(league_id)
        / str(season)
        / f"week_{week_index:02d}"
        / f"approved_v{version}"
    )

def write_latest_approved_pointer(approved_dir: Path, artifact) -> None:
    """
    Writes latest_approved.json in the parent week directory.
    Example:
      approved_dir = .../week_06/approved_v11
      writes        .../week_06/latest_approved.json
    """
    week_dir = approved_dir.parent
    pointer_path = week_dir / "latest_approved.json"

    data = {
        "version": artifact.version,
        "path": approved_dir.name,  # e.g. "approved_v11"
        "approved_by": artifact.approved_by,
        "approved_at": artifact.approved_at,
        "selection_fingerprint": artifact.selection_fingerprint,
        "window_start": artifact.window_start,
        "window_end": artifact.window_end,
    }

    pointer_path.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.out_dir and not args.out_root:
        raise SystemExit("ERROR: Must specify either --out-dir or --out-root")

    if args.out_dir and args.out_root:
        raise SystemExit("ERROR: Specify only one of --out-dir or --out-root")

    # Step 1: fetch approved artifact (needed for version)
    artifact = fetch_latest_approved_weekly_recap(
        db_path=args.db,
        league_id=str(args.league_id),
        season=int(args.season),
        week_index=int(args.week_index),
        version=args.version,
    )

    # Step 2: determine output directory
    if args.out_root:
        out_dir = _canonical_out_dir(
            Path(args.out_root),
            artifact.league_id,
            artifact.season,
            artifact.week_index,
            artifact.version,
        )
    else:
        out_dir = Path(args.out_dir)

    # Step 3: write export
    manifest = write_approved_weekly_recap_export_bundle(
        artifact,
        out_dir=out_dir,
        deterministic=(not args.non_deterministic),
    )

    write_latest_approved_pointer(out_dir, artifact)

    print("export_approved: OK")
    print(f"out_dir: {manifest.out_dir}")
    print(f"recap_md: {manifest.recap_md}")
    print(f"recap_json: {manifest.recap_json}")
    print(f"metadata_json: {manifest.metadata_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
