from __future__ import annotations

from pathlib import Path


TARGET = Path("src/squadvault/recaps/weekly_recap_lifecycle.py")

ANCHOR = "    path = _get_active_artifact_path(db_path, league_id, season, week_index)\n"
MARKER = "    # --- Clean-room safety: materialize ACTIVE recap JSON if missing (v1) ---\n"

INSERT = """\
    # --- Clean-room safety: materialize ACTIVE recap JSON if missing (v1) ---
    # CI runners start from a clean checkout; artifacts/ may not exist yet.
    # We must not assume recap_vNN.json is already present on disk.
    from pathlib import Path
    import json
    import re

    p = Path(path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

        # Derive recap_version from filename (recap_v01.json -> 1), fail closed if unknown.
        m = re.search(r"recap_v(\\d+)\\.json$", p.name)
        if not m:
            raise SystemExit(f"Active recap artifact path has unexpected filename: {path}")
        recap_version = int(m.group(1))

        selection_fingerprint, window_start, window_end = _get_recap_run_trace(
            db_path, league_id, season, week_index
        )

        # Minimal deterministic recap artifact (no event invention).
        artifact = {
            "league_id": league_id,
            "season": season,
            "week_index": week_index,
            "recap_version": recap_version,
            "window": {"start": window_start, "end": window_end},
            "selection": {
                "fingerprint": selection_fingerprint,
                "event_count": 0,
                "counts_by_type": {},
                "canonical_ids": [],
            },
        }

        with open(p, "w", encoding="utf-8") as f:
            json.dump(artifact, f, sort_keys=True)
            f.write("\\n")
    # --- /Clean-room safety ---
"""


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    if MARKER in text:
        print("OK: already patched (marker present).")
        return

    idx = text.find(ANCHOR)
    if idx == -1:
        raise SystemExit("ERROR: could not find anchor line in generate_weekly_recap_draft()")

    insert_at = idx + len(ANCHOR)
    new_text = text[:insert_at] + INSERT + "\n" + text[insert_at:]

    TARGET.write_text(new_text, encoding="utf-8")
    print("OK: patched weekly_recap_lifecycle.py to materialize ACTIVE recap JSON (v1)")


if __name__ == "__main__":
    main()
