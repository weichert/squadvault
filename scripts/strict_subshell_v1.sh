#!/usr/bin/env bash
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
