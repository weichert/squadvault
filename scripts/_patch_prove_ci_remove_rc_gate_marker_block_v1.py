from __future__ import annotations

from pathlib import Path
import sys

DOC = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: rivalry_chronicle_output_contract (v1) begin"
END   = "# SV_GATE: rivalry_chronicle_output_contract (v1) end"

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing file: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8")

    has_begin = BEGIN in src
    has_end = END in src

    # Already clean
    if not has_begin and not has_end:
        return 0

    # Safety: refuse partial marker situations
    if has_begin != has_end:
        print("ERROR: refused to patch (marker block is incomplete).", file=sys.stderr)
        print(f"BEGIN present={has_begin} END present={has_end}", file=sys.stderr)
        return 3

    lines = src.splitlines(keepends=True)

    out: list[str] = []
    in_block = False
    removed = False

    for ln in lines:
        if not in_block and BEGIN in ln:
            in_block = True
            removed = True
            continue
        if in_block:
            if END in ln:
                in_block = False
            continue
        out.append(ln)

    if in_block:
        print("ERROR: refused to patch (BEGIN found but END never encountered during scan).", file=sys.stderr)
        return 4

    new_src = "".join(out)
    if new_src != src:
        DOC.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
