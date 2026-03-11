from __future__ import annotations

from pathlib import Path
import sys

FILES = [
    Path("scripts/_patch_contract_linkage_general_gate_v1.py"),
    Path("scripts/_patch_gate_contract_linkage_bash3_compat_v1.py"),
    Path("scripts/_patch_remove_placeholder_contract_markers_v1.py"),
    Path("scripts/gate_contract_linkage_v1.sh"),
]

PREFIXES = (
    "SV_CONTRACT_NAME:",
    "SV_CONTRACT_DOC_PATH:",
)

def strip_markers(txt: str) -> str:
    out_lines = []
    for line in txt.splitlines(True):
        s = line.lstrip()
        if any(s.startswith(p) for p in PREFIXES):
            continue
        out_lines.append(line)
    return "".join(out_lines)

def main() -> int:
    for p in FILES:
        if not p.exists():
            print(f"ERR: missing file: {p}", file=sys.stderr)
            return 2
        before = p.read_text(encoding="utf-8")
        after = strip_markers(before)
        if after != before:
            p.write_text(after, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
