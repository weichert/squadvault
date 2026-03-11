from __future__ import annotations

import re
from pathlib import Path

GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not GATE.exists():
        die(f"missing {GATE}")

    text = GATE.read_text(encoding="utf-8")

    # If we already use grep -oE to extract scripts/gate_*.sh anywhere (non-comment),
    # assume this gate already supports direct invocation style.
    if re.search(r"grep\s+-oE\s+['\"]scripts/gate_", text):
        return

    # Heuristic patch: replace the "executed gates" extraction pipeline(s) so they
    # find gate paths regardless of "bash " prefix AND inside command substitutions.
    #
    # We do this by:
    #   - filtering out comment lines
    #   - extracting gate paths via grep -oE 'scripts/gate_...\.sh'
    #
    # This is robust to:
    #   scripts/gate_x.sh ...
    #   bash scripts/gate_x.sh ...
    #   VAR="$(scripts/gate_x.sh begin)"
    #
    # It will NOT count commented references because of the grep -vE '^\s*#' filter.
    replacement_block = r"""# SV_PATCH: executed gate detection accepts direct invocations (v1)
executed_gates="$(
  grep -vE '^\s*#' scripts/prove_ci.sh \
    | grep -oE 'scripts/gate_[A-Za-z0-9_]+\.sh' \
    | sort -u
)"
# SV_PATCH: executed gate detection accepts direct invocations (v1)
"""

    # Try to find an existing assignment that populates executed gates. Common patterns:
    #   executed_gates="$( ... grep ... bash scripts/gate_ ... )"
    #   executed="$( ... )"
    #
    # We patch the *first* matching block that assigns executed gates.
    patterns = [
        # executed_gates="...$( ... )"
        r'(?ms)^\s*executed_gates\s*=\s*"\$\(\s*.*?\n\)"\s*\n',
        # executed="...$( ... )"
        r'(?ms)^\s*executed\s*=\s*"\$\(\s*.*?\n\)"\s*\n',
        # executed_gates=$( ... )
        r'(?ms)^\s*executed_gates\s*=\s*\$\(\s*.*?\n\)\s*\n',
        # executed=$( ... )
        r'(?ms)^\s*executed\s*=\s*\$\(\s*.*?\n\)\s*\n',
    ]

    new_text = text
    patched = False
    for pat in patterns:
        m = re.search(pat, new_text)
        if m:
            new_text = new_text[: m.start()] + replacement_block + new_text[m.end() :]
            patched = True
            break

    if not patched:
        # Fallback: insert the replacement block near the top after strict mode.
        lines = new_text.splitlines(keepends=True)
        ins = None
        for i, line in enumerate(lines):
            if line.strip() == "set -euo pipefail":
                ins = i + 1
                break
        if ins is None:
            die("could not locate strict mode line for fallback insertion")
        lines.insert(ins, "\n" + replacement_block + "\n")
        new_text = "".join(lines)

    if new_text == text:
        return

    GATE.write_text(new_text, encoding="utf-8")

if __name__ == "__main__":
    main()
