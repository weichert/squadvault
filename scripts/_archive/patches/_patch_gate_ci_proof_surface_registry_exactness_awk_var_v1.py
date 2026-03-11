from __future__ import annotations

from pathlib import Path
import sys

GATE = Path("scripts/gate_ci_proof_surface_registry_exactness_v1.sh")

OLD = """\
block="$(awk -v b="${BEGIN}" -v e="${END}" '
  $0==b {in=1; next}
  $0==e {in=0; exit}
  in==1 {print}
' "${DOC}")"
"""

NEW = """\
block="$(awk -v b="${BEGIN}" -v e="${END}" '
  $0==b {inside=1; next}
  $0==e {inside=0; exit}
  inside==1 {print}
' "${DOC}")"
"""

def main() -> int:
    if not GATE.exists():
        print(f"ERROR: missing {GATE}", file=sys.stderr)
        return 1
    text = GATE.read_text(encoding="utf-8")

    if NEW in text:
        print("OK: awk state var already canonical (inside).")
        return 0

    if OLD not in text:
        print("ERROR: expected awk block not found; refuse (protect against drift).", file=sys.stderr)
        return 1

    updated = text.replace(OLD, NEW)
    GATE.write_text(updated, encoding="utf-8")
    print(f"UPDATED: {GATE}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
