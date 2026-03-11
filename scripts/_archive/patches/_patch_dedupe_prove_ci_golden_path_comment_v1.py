#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

DUP_LINE = "# If prove_golden_path.sh already has flags, pass them here; otherwise we patch it next.\n"


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    lines = TARGET.read_text(encoding="utf-8").splitlines(True)

    # Remove immediate duplicate of the exact comment line (keep the first).
    out: list[str] = []
    removed = 0
    i = 0
    while i < len(lines):
        out.append(lines[i])
        if lines[i] == DUP_LINE and i + 1 < len(lines) and lines[i + 1] == DUP_LINE:
            removed += 1
            i += 2
            continue
        i += 1

    if removed:
        TARGET.write_text("".join(out), encoding="utf-8")

    # Postcondition: never two adjacent DUP_LINE
    post = TARGET.read_text(encoding="utf-8")
    if DUP_LINE + DUP_LINE in post:
        raise SystemExit("ERROR: postcondition failed: duplicate comment still present")

    print("=== Patch: dedupe prove_ci golden path comment (v1) ===")
    print(f"target={TARGET} removed={removed}")


if __name__ == "__main__":
    main()
