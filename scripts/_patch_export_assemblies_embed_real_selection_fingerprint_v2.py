#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py")
SENTINEL = "SV_PATCH_EXPORT_ASSEMBLIES_FORCE_DATA_SELECTION_FP_V2"


def _die(msg: str) -> None:
    raise SystemExit(msg)


def main() -> None:
    if not TARGET.exists():
        _die(f"ERROR: missing target: {TARGET}")

    pre = TARGET.read_text(encoding="utf-8")

    if SENTINEL in pre:
        print(f"OK: already patched: {TARGET.name} ({SENTINEL})")
        return

    if "_effective_selection_fp(" not in pre:
        _die(
            "ERROR: v1 helper _effective_selection_fp not found. "
            "Apply v1 first (embed real selection_fingerprint) then rerun v2."
        )

    anchor = "selection_fp = _effective_selection_fp(conn, league_id, season, week_index, str(data.get(\"selection_fingerprint\") or \"\"))"
    if anchor not in pre:
        anchor2 = "selection_fp = _effective_selection_fp(conn, league_id, season, week_index, str(data.get('selection_fingerprint') or ''))"
        if anchor2 not in pre:
            _die("ERROR: could not find v1 selection_fp assignment to anchor v2 insertion")
        anchor = anchor2

    lines = pre.splitlines(True)
    out = []
    inserted = False

    for line in lines:
        out.append(line)
        if (not inserted) and (anchor in line):
            indent = line.split("selection_fp", 1)[0]
            out.append(f"{indent}# {SENTINEL}\n")
            out.append(f"{indent}# Force real selection_fingerprint back into data for all downstream render paths.\n")
            out.append(f"{indent}data['selection_fingerprint'] = selection_fp\n")
            inserted = True

    if not inserted:
        _die("ERROR: failed to insert v2 block")

    post = "".join(out)

    if SENTINEL not in post:
        _die("ERROR: postcondition failed: sentinel missing after patch")
    if "data['selection_fingerprint'] = selection_fp" not in post:
        _die("ERROR: postcondition failed: data injection missing after patch")

    TARGET.write_text(post, encoding="utf-8")
    print(f"OK: patched {TARGET} (force data['selection_fingerprint']=selection_fp).")


if __name__ == "__main__":
    main()
