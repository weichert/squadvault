from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CI = REPO_ROOT / "scripts" / "prove_ci.sh"
PROVE = REPO_ROOT / "scripts" / "prove_signal_scout_tier1_type_a_v1.sh"


PROVE_CONTENT = """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"

echo "=== Proof: Signal Scout Tier-1 Type A invariants (v1) ==="
echo "    repo_root=${REPO_ROOT}"

# Run only the signal taxonomy Type A validation tests (canonical enforcement surface).
"${REPO_ROOT}/scripts/py" -m pytest -q "${REPO_ROOT}/Tests/validation/signals"

echo "OK: Signal Scout Tier-1 Type A invariants proved (v1)"
"""


def _ensure_prove_script() -> None:
    if PROVE.exists():
        existing = PROVE.read_text(encoding="utf-8")
        if existing == PROVE_CONTENT:
            return
        # Fail closed: do not “merge” content; require deterministic exactness.
        raise SystemExit(
            f"ERROR: {PROVE} exists but content differs; refusing to overwrite"
        )

    PROVE.write_text(PROVE_CONTENT, encoding="utf-8")
    st = os.stat(PROVE)
    os.chmod(PROVE, st.st_mode | 0o111)  # ensure executable


def _wire_into_ci() -> None:
    if not CI.exists():
        raise SystemExit(f"ERROR: missing CI runner: {CI}")

    ci_text = CI.read_text(encoding="utf-8")

    call_line = "bash scripts/prove_signal_scout_tier1_type_a_v1.sh\n"
    if call_line in ci_text:
        return

    anchor = "bash scripts/prove_version_presentation_navigation_type_a_v1.sh\n"
    idx = ci_text.find(anchor)
    if idx == -1:
        raise SystemExit("ERROR: could not find CI anchor line for wiring")

    insert_at = idx + len(anchor)
    ci_text_new = ci_text[:insert_at] + "\n" + call_line + ci_text[insert_at:]
    CI.write_text(ci_text_new, encoding="utf-8")


def main() -> None:
    _ensure_prove_script()
    _wire_into_ci()
    print("OK: added + wired prove_signal_scout_tier1_type_a_v1 (v1)")


if __name__ == "__main__":
    main()
