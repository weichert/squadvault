#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/prove_eal_calibration_type_a_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    # Match the exact mapfile block:
    # mapfile -t eal_tests < <(
    #   ...
    # )
    pat = re.compile(
        r"""(?ms)
(^[ \t]*mapfile[ \t]+-t[ \t]+eal_tests[ \t]*<[ \t]*<\(\n)
(.*?)
(\n\)[ \t]*\n)
"""
    )

    m = pat.search(s)
    if not m:
        raise SystemExit(
            "ERROR: could not find the expected mapfile block for eal_tests.\n"
            "Paste lines 40-65 again if this persists."
        )

    body = m.group(2).rstrip("\n")

    repl = (
        "eal_tests=()\n"
        "while IFS= read -r __line; do\n"
        "  eal_tests+=(\"$__line\")\n"
        "done < <(\n"
        f"{body}\n"
        ")\n"
        "unset __line\n"
    )

    s2 = s[: m.start()] + repl + s[m.end() :]
    TARGET.write_text(s2, encoding="utf-8")
    print("OK: removed mapfile for eal_tests (bash3-safe, v3).")

if __name__ == "__main__":
    main()
