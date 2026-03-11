from __future__ import annotations

from pathlib import Path

HELPER = Path("scripts/strict_subshell_v1.sh")
DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

HELPER_TEXT = """#!/usr/bin/env bash
# SquadVault — strict subshell helper (v1)
#
# Purpose:
#   Run a command under Bash with `set -euo pipefail` *without* polluting the caller's shell
#   (useful when your interactive shell is zsh and `set -u` can break session hooks).
#
# Usage:
#   ./scripts/strict_subshell_v1.sh 'grep -n "foo" file | head -n 5'
#
# Notes:
#   - The command runs in a fresh bash -lc environment.
#   - Keep the command deterministic (avoid time, random, network).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: strict_subshell_v1.sh '<command>'" >&2
  exit 2
fi

cmd="$1"
shift || true

# If extra args are provided, append them shell-escaped-ish (best-effort) to avoid surprises.
# Primary intended usage is a single quoted command string.
if [[ $# -gt 0 ]]; then
  for a in "$@"; do
    cmd="${cmd} $(printf "%q" "$a")"
  done
fi

exec bash -lc "set -euo pipefail; ${cmd}"
"""

DOC_NOTE = """
## Operator Safety Note (Build Mode)

When running inspection commands from interactive shells (e.g. zsh), avoid leaking `set -u` into your session.
Use either a subshell:

- `( set -euo pipefail; <command> )`

or the canonical helper:

- `./scripts/strict_subshell_v1.sh '<command>'`
""".strip() + "\n"

# Anchor on the NAC bullet marker block that is known to exist.
DOC_ANCHOR = "<!-- /SV_PATCH: nac fingerprint preflight doc (v1) -->"

def ensure_helper() -> None:
    if HELPER.exists():
        # If already identical, no-op; if drifted, fail closed.
        existing = HELPER.read_text(encoding="utf-8")
        if existing != HELPER_TEXT:
            raise SystemExit(f"ERROR: {HELPER} exists but content differs; refusing to overwrite")
        return
    HELPER.write_text(HELPER_TEXT, encoding="utf-8")
    HELPER.chmod(0o755)

def patch_doc() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: missing doc target: {DOC}")

    text = DOC.read_text(encoding="utf-8")
    if "Operator Safety Note (Build Mode)" in text:
        return

    if DOC_ANCHOR not in text:
        raise SystemExit("ERROR: doc anchor not found (expected NAC bullet marker); refusing to guess insertion point")

    text = text.replace(DOC_ANCHOR, DOC_ANCHOR + "\n\n" + DOC_NOTE, 1)
    DOC.write_text(text, encoding="utf-8")

def main() -> int:
    ensure_helper()
    patch_doc()
    print(f"OK: helper present: {HELPER}")
    print(f"OK: doc patched: {DOC}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
