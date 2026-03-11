from __future__ import annotations
from pathlib import Path

TARGET = Path(".gitignore")
ALLOWLINE = "!scripts/_patch_prove_golden_path_pin_pytest_list_v3.py"
HEADER = "# Canonical patchers (DO track these)"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    s = TARGET.read_text(encoding="utf-8")
    if ALLOWLINE in s:
        return

    lines = s.splitlines(True)
    insert_at = None
    for i, line in enumerate(lines):
        if line.rstrip("\n") == HEADER:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit(f"ERROR: could not find header: {HEADER}")

    lines.insert(insert_at, ALLOWLINE + "\n")
    TARGET.write_text("".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
