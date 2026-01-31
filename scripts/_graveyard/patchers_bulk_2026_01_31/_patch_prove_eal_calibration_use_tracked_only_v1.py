#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_eal_calibration_type_a_v1.sh")

MARKER = "SV_PATCH: tracked-only pytest list (no tests/ lowercase pass)"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if MARKER in s:
        print("OK: tracked-only patch already applied.")
        return

    lines = s.splitlines()

    # Strategy:
    # - Find the block that prints "Tracked EAL test files: ${#eal_tests[@]}"
    # - Ensure the pytest invocation uses "${eal_tests[@]}" and remove any later
    #   invocation that hardcodes tests/ paths.
    #
    # We do the smallest safe thing: after the "Tracked EAL test files" block,
    # enforce exactly one pytest run using eal_tests.

    out = []
    i = 0
    injected = False

    while i < len(lines):
        ln = lines[i]

        # Remove any explicit pytest calls that reference "/tests/test_" (lowercase tests/)
        # These are the ones causing "not found".
        if ("pytest" in ln or "py -m pytest" in ln) and "/tests/test_" in ln:
            # drop this line and any immediate continuation lines ending with '\'
            i += 1
            while i < len(lines) and lines[i].rstrip().endswith("\\"):
                i += 1
            continue

        # Also remove lines that set TEST_DIR=tests (lowercase) in this script,
        # since it misleads downstream path construction.
        if ln.strip().startswith('TEST_DIR=') and 'tests' in ln and 'Tests' not in ln:
            # skip this line
            i += 1
            continue

        out.append(ln)

        # After the guard that ensures eal_tests is non-empty, inject one canonical run.
        if not injected and ln.strip().startswith('if [[ ${#eal_tests[@]} -eq 0 ]]'):
            # Copy through the entire "if ... fi" block unchanged.
            i += 1
            while i < len(lines):
                out.append(lines[i])
                if lines[i].strip() == "fi":
                    break
                i += 1

            out.append("")
            out.append(f"# {MARKER}")
            out.append("echo \"Running tracked EAL tests only (git ls-files)\"")
            out.append("./scripts/py -m pytest -q \"${eal_tests[@]}\"")
            out.append(f"# /{MARKER}")
            injected = True
            i += 1
            continue

        i += 1

    if not injected:
        raise SystemExit(
            "ERROR: could not locate the eal_tests empty-check block to anchor the patch.\n"
            "Paste the whole scripts/prove_eal_calibration_type_a_v1.sh if this persists."
        )

    TARGET.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("OK: patched prove_eal_calibration_type_a_v1.sh to run tracked tests only.")

if __name__ == "__main__":
    main()
