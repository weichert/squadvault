from __future__ import annotations

import re
from pathlib import Path

GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

CANON_BLOCK = r"""# SV_PATCH: executed gate detection accepts direct invocations (v2)
executed_gates="$(
  grep -vE '^\s*#' scripts/prove_ci.sh \
    | grep -oE 'scripts/gate_[A-Za-z0-9_]+\.sh' \
    | sort -u
)"
# Back-compat: older versions used $executed in comparisons
executed="${executed_gates}"
# SV_PATCH: executed gate detection accepts direct invocations (v2)
"""

def strip_other_assignments(text: str) -> str:
    # Remove any existing executed_gates/executed assignments (best effort), so we control the source of truth.
    #
    # Matches:
    #   executed_gates="$( ... )"
    #   executed="$( ... )"
    #   executed_gates=$( ... )
    #   executed=$( ... )
    #
    # We intentionally do NOT remove "executed=" inside comments (handled by multiline anchor + non-comment structure).
    patterns = [
        r'(?ms)^\s*executed_gates\s*=\s*"\$\(\s*.*?\n\)"\s*\n',
        r'(?ms)^\s*executed\s*=\s*"\$\(\s*.*?\n\)"\s*\n',
        r'(?ms)^\s*executed_gates\s*=\s*\$\(\s*.*?\n\)\s*\n',
        r'(?ms)^\s*executed\s*=\s*\$\(\s*.*?\n\)\s*\n',
        r'(?m)^\s*executed_gates\s*=\s*".*"\s*\n',
        r'(?m)^\s*executed\s*=\s*".*"\s*\n',
        r'(?m)^\s*executed_gates\s*=\s*.*\s*\n',
        r'(?m)^\s*executed\s*=\s*.*\s*\n',
    ]
    out = text
    for pat in patterns:
        out = re.sub(pat, "", out)
    return out

def insert_after_strict_mode(text: str) -> str:
    lines = text.splitlines(keepends=True)
    ins = None
    for i, line in enumerate(lines):
        if line.strip() == "set -euo pipefail":
            ins = i + 1
            break
    if ins is None:
        die("could not find strict-mode line: set -euo pipefail")

    # Avoid double-inserting
    if "SV_PATCH: executed gate detection accepts direct invocations (v2)" in text:
        return text

    lines.insert(ins, "\n" + CANON_BLOCK + "\n")
    return "".join(lines)

def main() -> None:
    if not GATE.exists():
        die(f"missing {GATE}")

    original = GATE.read_text(encoding="utf-8")

    text = original
    text = strip_other_assignments(text)
    text = insert_after_strict_mode(text)

    if text == original:
        return

    GATE.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
