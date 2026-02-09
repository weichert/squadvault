from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/_patch_contract_linkage_general_gate_v1.py")

OLD = 'RC_CANDIDATES = sorted(\n    [Path(p) for p in glob.glob(str(SCRIPTS / "gate_*contract*linkage*rc*_v*.sh"))]\n)\n'
NEW = 'RC_CANDIDATES = sorted(\n    [Path(p) for p in glob.glob(str(SCRIPTS / "gate_*rivalry*chronicle*contract*linkage*_v*.sh"))]\n)\n'

def main() -> int:
    if not TARGET.exists():
        print(f"ERR: missing target: {TARGET}", file=sys.stderr)
        return 2

    txt = TARGET.read_text(encoding="utf-8")
    if NEW in txt:
        # already patched
        return 0

    if OLD not in txt:
        print("ERR: expected anchored block not found in target; refusing to guess.", file=sys.stderr)
        return 2

    TARGET.write_text(txt.replace(OLD, NEW), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
