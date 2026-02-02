from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(".gitignore")

NEW = [
    "scripts/_patch_export_squadvault_test_db_in_prove_ci_v1.py",
    "scripts/_patch_tests_use_squadvault_test_db_env_v1.py",
    "scripts/_patch_allowlist_new_patchers_for_ci_db_fix_v1.py",
]


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def is_allowlist_line(ln: str) -> bool:
    s = ln.strip()
    return s.startswith("scripts/_patch_") and s.endswith(".py") and " " not in s and "\t" not in s


def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    lines = s.splitlines(keepends=True)

    blocks: list[tuple[int, int]] = []
    i = 0
    n = len(lines)
    while i < n:
        if is_allowlist_line(lines[i]):
            start = i
            i += 1
            while i < n and is_allowlist_line(lines[i]):
                i += 1
            end = i
            blocks.append((start, end))
        else:
            i += 1

    if not blocks:
        die("could not find any contiguous allowlist block of scripts/_patch_*.py in .gitignore")

    blocks.sort(key=lambda t: (t[1] - t[0]), reverse=True)
    start, end = blocks[0]

    existing = [lines[j].strip() for j in range(start, end)]
    combined = sorted(set(existing + NEW))

    out_lines = lines[:start] + [x + "\n" for x in combined] + lines[end:]
    out = "".join(out_lines)

    if out == s:
        print("OK: .gitignore already contains required allowlist entries (no changes)")
        return

    TARGET.write_text(out, encoding="utf-8")
    print("OK: updated .gitignore patcher allowlist block (deduped + sorted)")


if __name__ == "__main__":
    main()
