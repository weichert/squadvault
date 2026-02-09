from __future__ import annotations

from pathlib import Path
import sys

FILES = [
    Path("scripts/_patch_contract_linkage_general_gate_v1.py"),
    Path("scripts/_patch_gate_contract_linkage_bash3_compat_v1.py"),
    Path("scripts/_patch_remove_placeholder_contract_markers_v1.py"),
    Path("scripts/gate_contract_linkage_v1.sh"),
]

TOKEN = "<repo-relative path>"

def main() -> int:
    for p in FILES:
        if not p.exists():
            print(f"ERR: missing file: {p}", file=sys.stderr)
            return 2
        txt = p.read_text(encoding="utf-8")
        if TOKEN in txt:
            p.write_text(txt.replace(TOKEN, ""), encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
