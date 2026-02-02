from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")
FORBIDDEN = "pytest -q Tests"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    if FORBIDDEN not in s:
        return  # idempotent no-op

    out_lines: list[str] = []
    removed = 0
    for line in s.splitlines(True):
        if line.strip() == FORBIDDEN:
            removed += 1
            continue
        out_lines.append(line)

    if removed == 0:
        # Present as substring but not as a full-line invocation; refuse for safety.
        raise SystemExit("ERROR: found forbidden text but not as a standalone line; refusing")

    new = "".join(out_lines)

    # Hard postcondition
    if FORBIDDEN in new:
        raise SystemExit("ERROR: forbidden invocation still present after attempted removal")

    TARGET.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    main()
