#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_eal_calibration_type_a_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    # Preserve original newlines as best we can
    raw = TARGET.read_text(encoding="utf-8")
    # Normalize only for scanning; write back with '\n' (repo scripts are typically LF)
    lines = raw.splitlines()

    # Find start line containing the exact mapfile invocation
    start = None
    for i, ln in enumerate(lines):
        if "mapfile" in ln and "-t" in ln and "eal_tests" in ln and "< <(" in ln:
            start = i
            break

    if start is None:
        print("OK: no mapfile eal_tests block found; nothing to patch.")
        return

    # Find the closing ')' line for the process substitution
    end = None
    for j in range(start + 1, len(lines)):
        stripped = lines[j].strip()
        # Accept: ")" or ") <anything>" (e.g., ') | sort' is possible, though not here)
        if stripped == ")" or stripped.startswith(") " ) or stripped.startswith(")#") or stripped.startswith(") #") or stripped.startswith(")|") or stripped.startswith(") |"):
            end = j
            break

    if end is None:
        raise SystemExit(
            "ERROR: found mapfile start but could not find closing ')' for < <( ... ) block.\n"
            "DEBUG: mapfile line was:\n"
            f"{lines[start]}\n"
        )

    body_lines = lines[start + 1 : end]
    # Build replacement using the original body lines verbatim
    replacement: list[str] = [
        "eal_tests=()",
        'while IFS= read -r __line; do',
        '  eal_tests+=("$__line")',
        "done < <(",
    ]
    replacement.extend(body_lines)
    replacement.extend([
        ")",
        "unset __line",
    ])

    new_lines = []
    new_lines.extend(lines[:start])
    new_lines.extend(replacement)
    new_lines.extend(lines[end + 1 :])

    TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("OK: removed mapfile block for eal_tests (bash3-safe, v4).")

if __name__ == "__main__":
    main()
