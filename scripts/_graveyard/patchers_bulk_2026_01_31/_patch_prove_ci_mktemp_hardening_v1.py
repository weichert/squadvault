#!/usr/bin/env python3
from __future__ import annotations

import io
import os
import sys

def die(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2

def main() -> int:
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    target = os.path.join(repo_root, "scripts", "prove_ci.sh")
    if not os.path.exists(target):
        return die(f"missing target: {target}")

    with io.open(target, "r", encoding="utf-8") as f:
        src = f.read()

    # Anchor: after set -euo pipefail (already present in your diff)
    needle = "set -euo pipefail\n"
    if needle not in src:
        return die("could not find 'set -euo pipefail' anchor")

    if "SV_TMPDIR=" in src:
        print("OK: SV_TMPDIR already present (no-op or previously patched).")

    insert_block = (
        "\n"
        "# --- Temp workspace normalization (bash 3.2 safe) ---\n"
        "SV_TMPDIR=\"${TMPDIR:-/tmp}\"\n"
        "SV_TMPDIR=\"${SV_TMPDIR%/}\"\n"
        "# --- /Temp workspace normalization ---\n"
        "\n"
    )

    # Insert tempdir normalization immediately after set -euo pipefail,
    # but only if not already present.
    if "SV_TMPDIR=" not in src:
        src = src.replace(needle, needle + insert_block)

    # Patch mktemp lines to use SV_TMPDIR.
    # 1) STATEFILE
    old_state = 'STATEFILE="$(mktemp "${TMPDIR:-/tmp}/squadvault_fixture_state.XXXXXX")"'
    new_state = 'STATEFILE="$(mktemp "${SV_TMPDIR}/squadvault_fixture_state.XXXXXX")"'
    if old_state in src:
        src = src.replace(old_state, new_state)
    elif new_state not in src:
        return die("could not locate STATEFILE mktemp line to patch")

    # Add assertion immediately after STATEFILE assignment (only once)
    state_assert = (
        "\n"
        "if [[ -z \"${STATEFILE}\" ]]; then\n"
        "  echo \"ERROR: mktemp failed to create STATEFILE\" >&2\n"
        "  exit 2\n"
        "fi\n"
    )
    if "mktemp failed to create STATEFILE" not in src:
        src = src.replace(new_state, new_state + state_assert)

    # 2) WORK_DB
    old_db = 'WORK_DB="$(mktemp "${TMPDIR:-/tmp}/squadvault_ci_workdb.XXXXXX.sqlite")"'
    new_db = 'WORK_DB="$(mktemp "${SV_TMPDIR}/squadvault_ci_workdb.XXXXXX.sqlite")"'
    if old_db in src:
        src = src.replace(old_db, new_db)
    elif new_db not in src:
        return die("could not locate WORK_DB mktemp line to patch")

    db_assert = (
        "\n"
        "  if [[ -z \"${WORK_DB}\" ]]; then\n"
        "    echo \"ERROR: mktemp failed to create WORK_DB\" >&2\n"
        "    exit 2\n"
        "  fi\n"
    )
    if "mktemp failed to create WORK_DB" not in src:
        src = src.replace(new_db, new_db + db_assert)

    # Compose EXIT trap: replace the guardrail trap with an exit function that:
    # - checks repo cleanliness after
    # - removes temp files created outside repo
    old_trap = "trap './scripts/check_repo_cleanliness_ci.sh --phase after' EXIT"
    if old_trap in src:
        exit_fn = (
            "\n"
            "sv_ci_on_exit() {\n"
            "  # Repo cleanliness guardrail (no cleanup / no masking)\n"
            "  ./scripts/check_repo_cleanliness_ci.sh --phase after\n"
            "  # Safe temp cleanup (outside repo)\n"
            "  rm -f \"${WORK_DB:-}\" \"${STATEFILE:-}\" >/dev/null 2>&1 || true\n"
            "}\n"
            "trap 'sv_ci_on_exit' EXIT\n"
        )
        src = src.replace(old_trap, exit_fn.strip("\n"))
    else:
        # If trap already customized, avoid guessing.
        if "check_repo_cleanliness_ci.sh --phase after" in src:
            return die("found existing after-cleanliness reference but could not patch trap deterministically")
        # Otherwise, nothing to do here.

    with io.open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)

    print("OK: patched scripts/prove_ci.sh (mktemp hardening + composed EXIT trap).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
