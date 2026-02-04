#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

# We anchor on the golden path strict block's closing "fi"
# and then replace everything after it with the canonical tail.
ANCHOR_RE = re.compile(r'^\s*fi\s*$', re.MULTILINE)

TAIL = """\
echo
echo "=== CI: Rivalry Chronicle end-to-end (fixture) ==="
SV_PROVE_TS_UTC="2026-01-01T00:00:00Z" bash scripts/prove_rivalry_chronicle_end_to_end_v1.sh \\
  --db "${WORK_DB}" \\
  --league-id 70985 \\
  --season 2024 \\
  --week-index 6 \\
  --approved-by "ci"

# --- Fixture immutability guard (CI) ---
./scripts/check_fixture_immutability_ci.sh verify "${STATEFILE}" "${fixture_files[@]}"
# --- /Fixture immutability guard (CI) ---

# --- CI debug: DB source summary ---
if [[ "${WORK_DB}" == "${FIXTURE_DB}" ]]; then
  echo "CI DB source: fixture (read-only path used)"
else
  echo "CI DB source: temp working copy (derived from fixture)"
  echo "  fixture_db=${FIXTURE_DB}"
  echo "  working_db=${WORK_DB}"
fi
# --- /CI debug ---

echo "OK: CI proof suite passed"
echo "OK: CI working tree remained clean (guardrail enforced)."
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    original = TARGET.read_text(encoding="utf-8")
    lines = original.splitlines(True)

    # Find the last 'fi' in the file (should be the golden path block)
    fi_indices = [i for i, ln in enumerate(lines) if ln.strip() == "fi"]
    if not fi_indices:
        raise SystemExit("ERROR: could not find any 'fi' line to anchor tail replacement")

    fi_i = fi_indices[-1]

    # Ensure the fi is part of golden path block by checking nearby context
    window = "".join(lines[max(0, fi_i - 10): fi_i + 1])
    if "prove_golden_path.sh" not in window:
        raise SystemExit("ERROR: last 'fi' does not appear to belong to golden path block")

    new_lines = []
    new_lines.extend(lines[:fi_i + 1])
    # Ensure exactly one newline after fi
    if not new_lines[-1].endswith("\n"):
        new_lines[-1] = new_lines[-1] + "\n"
    new_lines.append("\n")
    new_lines.append(TAIL)

    new_text = "".join(new_lines)

    changed = "yes" if new_text != original else "no"
    if changed == "yes":
        TARGET.write_text(new_text, encoding="utf-8")

    # Postconditions:
    post = TARGET.read_text(encoding="utf-8")
    if "prove_rivalry_chronicle_end_to_end_v1.sh" not in post:
        raise SystemExit("ERROR: postcondition failed: rivalry prove not present")
    if "check_fixture_immutability_ci.sh verify" not in post:
        raise SystemExit("ERROR: postcondition failed: fixture immutability verify not present")
    if not post.rstrip("\n").endswith('echo "OK: CI working tree remained clean (guardrail enforced)."'):
        raise SystemExit("ERROR: postcondition failed: missing final OK line")

    print("=== Patch: restore prove_ci tail with rivalry (v1) ===")
    print(f"target={TARGET} changed={changed}")

if __name__ == "__main__":
    main()
