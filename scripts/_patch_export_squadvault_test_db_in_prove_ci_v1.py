from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

EXPORT_LINE_WORK_DB = 'export SQUADVAULT_TEST_DB="$WORK_DB"\n'
EXPORT_LINE_working_db = 'export SQUADVAULT_TEST_DB="$working_db"\n'


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if "SQUADVAULT_TEST_DB" in s:
        die("SQUADVAULT_TEST_DB already present in scripts/prove_ci.sh; refusing to patch")

    lines = s.splitlines(keepends=True)

    idx = None
    mode = None

    for i, ln in enumerate(lines):
        if ln.startswith("WORK_DB="):
            idx = i
            mode = "WORK_DB"
            break

    if idx is None:
        for i, ln in enumerate(lines):
            if ln.startswith("working_db="):
                idx = i
                mode = "working_db"
                break

    if idx is None or mode is None:
        die("could not find WORK_DB= or working_db= assignment anchor in scripts/prove_ci.sh")

    insert_line = EXPORT_LINE_WORK_DB if mode == "WORK_DB" else EXPORT_LINE_working_db

    out_lines = lines[: idx + 1] + [insert_line] + lines[idx + 1 :]
    out = "".join(out_lines)

    if out == s:
        die("no-op patch (unexpected)")

    TARGET.write_text(out, encoding="utf-8")
    print("OK: exported SQUADVAULT_TEST_DB in scripts/prove_ci.sh")


if __name__ == "__main__":
    main()
