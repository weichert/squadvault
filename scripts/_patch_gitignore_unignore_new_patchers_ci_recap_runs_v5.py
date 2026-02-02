from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(".gitignore")
IGNORE_RULE = "scripts/_patch_*.py"

NEW_UNIGNORE = [
    "!scripts/_patch_move_squadvault_test_db_export_after_workdb_final_v3.py",
    "!scripts/_patch_gitignore_unignore_new_patchers_ci_recap_runs_v5.py",
]


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TARGET.exists():
        die("missing .gitignore")

    s = TARGET.read_text(encoding="utf-8")
    lines = s.splitlines(keepends=True)

    idx = None
    for i, ln in enumerate(lines):
        if ln.strip() == IGNORE_RULE:
            idx = i
            break
    if idx is None:
        die(f'could not find ignore rule anchor "{IGNORE_RULE}" in .gitignore')

    insert_at = idx + 1

    j = insert_at
    existing_block: list[str] = []
    while j < len(lines):
        t = lines[j].strip()
        if t.startswith("!scripts/_patch_") and t.endswith(".py") and " " not in t and "\t" not in t:
            existing_block.append(t)
            j += 1
            continue
        break

    combined = sorted(set(existing_block + NEW_UNIGNORE))

    out_lines = lines[:insert_at] + [x + "\n" for x in combined] + lines[insert_at + len(existing_block) :]
    out = "".join(out_lines)

    if out == s:
        print("OK: .gitignore already unignores recap_runs v5 patchers (no changes)")
        return

    TARGET.write_text(out, encoding="utf-8")
    print("OK: updated .gitignore to unignore recap_runs v5 patchers")


if __name__ == "__main__":
    main()
