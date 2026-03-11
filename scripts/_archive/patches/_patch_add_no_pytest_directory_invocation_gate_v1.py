from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
CI = REPO_ROOT / "scripts" / "prove_ci.sh"
GATE = REPO_ROOT / "scripts" / "check_no_pytest_directory_invocation.sh"

CALL = "bash scripts/check_no_pytest_directory_invocation.sh\n"


def _ensure_executable(path: Path) -> None:
    st = os.stat(path)
    os.chmod(path, st.st_mode | 0o111)


def _ensure_gate_exists() -> None:
    if not GATE.exists():
        raise SystemExit(f"ERROR: missing gate script (expected pre-created): {GATE}")
    _ensure_executable(GATE)


def _wire_into_ci() -> None:
    if not CI.exists():
        raise SystemExit(f"ERROR: missing CI runner: {CI}")

    text = CI.read_text(encoding="utf-8")
    if CALL in text:
        return

    # Wire near other static gates.
    anchor = "bash scripts/check_no_memory_reads.sh\n"
    idx = text.find(anchor)
    if idx == -1:
        raise SystemExit("ERROR: could not find wiring anchor in scripts/prove_ci.sh")

    insert_at = idx + len(anchor)
    new_text = text[:insert_at] + "\n" + CALL + text[insert_at:]
    CI.write_text(new_text, encoding="utf-8")


def main() -> None:
    _ensure_gate_exists()
    _wire_into_ci()
    print("OK: wired no-pytest-directory-invocation gate into prove_ci.sh (v1)")


if __name__ == "__main__":
    main()
