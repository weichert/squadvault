from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "patch_writing_room_intake_exclusions_v1.sh"

GUARDED_BLOCK_RE = re.compile(
    r"""
    ^if\ \[\[\ -n\ "\$\{PY_BIN\}"\ \]\];\ then\n
    (?:.*\n)*?
    ^fi\n
    """,
    re.M | re.X,
)

PYTEST_LINE_RE = re.compile(r"(^.*\bpytest\b.*$)", re.M)

def main() -> int:
    s = TARGET.read_text(encoding="utf-8")

    # 1) If we have multiple guarded blocks, keep only the first.
    blocks = list(GUARDED_BLOCK_RE.finditer(s))
    if len(blocks) >= 2:
        # Remove all but the first block.
        keep0 = blocks[0]
        out = []
        last = 0
        out.append(s[: keep0.end()])
        last = keep0.end()
        for b in blocks[1:]:
            out.append(s[last : b.start()])
            # skip block b
            last = b.end()
        out.append(s[last:])
        s2 = "".join(out)

        TARGET.write_text(s2, encoding="utf-8")
        print(f"OK: removed {len(blocks)-1} duplicate guarded pytest block(s) from {TARGET.relative_to(ROOT)}")
        return 0

    # 2) Otherwise, fall back to removing duplicate pytest *lines* (keep first occurrence)
    pytest_lines = PYTEST_LINE_RE.findall(s)
    if len(pytest_lines) <= 1:
        print("OK: no duplicate pytest invocations found; nothing to patch.")
        return 0

    # Keep first pytest line; remove subsequent identical/other pytest lines
    first_idx = s.find(pytest_lines[0])
    if first_idx == -1:
        raise SystemExit("ERROR: internal mismatch locating first pytest line")

    # Remove any later lines containing 'pytest'
    lines = s.splitlines(True)
    kept_first = False
    out_lines = []
    removed = 0
    for ln in lines:
        if "pytest" in ln:
            if not kept_first:
                out_lines.append(ln)
                kept_first = True
            else:
                removed += 1
                continue
        else:
            out_lines.append(ln)

    if removed == 0:
        print("OK: no removable duplicate pytest lines found; nothing to patch.")
        return 0

    TARGET.write_text("".join(out_lines), encoding="utf-8")
    print(f"OK: removed {removed} duplicate pytest invocation line(s) from {TARGET.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
