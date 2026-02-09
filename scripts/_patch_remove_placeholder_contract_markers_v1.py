from __future__ import annotations

from pathlib import Path
import sys

FILES = [
    Path("scripts/_patch_contract_linkage_general_gate_v1.py"),
    Path("scripts/_patch_gate_contract_linkage_bash3_compat_v1.py"),
    Path("scripts/gate_contract_linkage_v1.sh"),
]

PLACEHOLDER_DOC = "SV_CONTRACT_DOC_PATH: "
PLACEHOLDER_NAME = "SV_CONTRACT_NAME: <NAME>"
# Also handle any generic placeholder name variants if present
NAME_PREFIX = "SV_CONTRACT_NAME:"
DOC_PREFIX = "SV_CONTRACT_DOC_PATH:"


def strip_placeholders(txt: str) -> str:
    lines = txt.splitlines(True)
    out = []
    for line in lines:
        s = line.strip()
        if s == PLACEHOLDER_DOC:
            continue
        if s == PLACEHOLDER_NAME:
            continue
        # If someone wrote: SV_CONTRACT_DOC_PATH:  (with extra spaces)
        if s.startswith(DOC_PREFIX) and "" in s:
            continue
        # If someone wrote a placeholder name like: SV_CONTRACT_NAME: <...>
        if s.startswith(NAME_PREFIX) and "<" in s and ">" in s and "SV_CONTRACT_NAME:" in s:
            # only strip if it looks like a template placeholder
            if "<" in s and ">" in s:
                continue
        out.append(line)
    return "".join(out)


def main() -> int:
    changed = False
    for p in FILES:
        if not p.exists():
            print(f"ERR: missing file: {p}", file=sys.stderr)
            return 2
        before = p.read_text(encoding="utf-8")
        after = strip_placeholders(before)
        if after != before:
            p.write_text(after, encoding="utf-8")
            changed = True

    # Idempotent: allow no-op
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
