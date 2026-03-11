#!/usr/bin/env python3
from pathlib import Path
import os

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK = REPO_ROOT / "scripts" / "check_filesystem_ordering_determinism.sh"

NEW = """#!/usr/bin/env bash
set -euo pipefail

# === SquadVault: Filesystem Ordering Determinism Gate (v1.1) ===
# Goal: catch unordered filesystem iteration that can affect behavior/output.
# Scope: runtime + consumers (src/) and non-patcher ops scripts (scripts/).
#
# Waiver (explicit, reviewable):
#   # SV_ALLOW_UNSORTED_FS_ORDER

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

FAIL=0
say() { echo "$@"; }
warn() { echo "ERROR: $@" 1>&2; }

filter_exclusions() {
  # Filter out patchers/diagnostics + this gate itself.
  # (They are tooling, not runtime determinism surface.)
  grep -v -E 'scripts/(patch_|_patch_|_diag_).*' | \
  grep -v -E 'scripts/check_filesystem_ordering_determinism\\.sh'
}

grep_hits() {
  local label="$1"
  local re="$2"
  shift 2

  local hits
  hits="$(grep -R -n -E "${re}" "$@" 2>/dev/null || true)"

  if [ -n "${hits}" ]; then
    hits="$(printf "%s\\n" "${hits}" | filter_exclusions | grep -v "SV_ALLOW_UNSORTED_FS_ORDER" || true)"
  fi

  if [ -n "${hits}" ]; then
    warn "Filesystem ordering nondeterminism risk: ${label}"
    printf "%s\\n" "${hits}" 1>&2
    FAIL=1
  fi
}

TARGETS_SHELL="scripts"
TARGETS_PY="src scripts"

# --- Shell risk patterns ---
# Flag only when ls output is consumed structurally (not for display)
grep_hits "shell: 'ls | while read' (ls as data source; ordering/whitespace hazards)" \
  '(^|[[:space:];&(])ls([[:space:]].*)?[[:space:]]*\\|[[:space:]]*while[[:space:]]+read' \
  ${TARGETS_SHELL}

grep_hits "shell: 'ls | xargs' (ls as data source; ordering/whitespace hazards)" \
  '(^|[[:space:];&(])ls([[:space:]].*)?[[:space:]]*\\|[[:space:]]*xargs' \
  ${TARGETS_SHELL}

# find piped into while/read: high-risk traversal order
grep_hits "shell: 'find ... | while read' (traversal order)" \
  'find[[:space:]].*\\|[[:space:]]*while[[:space:]]+read' \
  ${TARGETS_SHELL}

# --- Python risk patterns ---
grep_hits "python: os.listdir() used (must sort)" \
  'os\\.listdir[[:space:]]*\\(' \
  ${TARGETS_PY}

grep_hits "python: glob.glob() used (must sort)" \
  'glob\\.glob[[:space:]]*\\(' \
  ${TARGETS_PY}

grep_hits "python: Path.glob()/rglob() used (must sort)" \
  '\\.r?glob[[:space:]]*\\(' \
  ${TARGETS_PY}

grep_hits "python: os.walk() used (must sort dirnames/filenames)" \
  'os\\.walk[[:space:]]*\\(' \
  ${TARGETS_PY}

if [ "${FAIL}" -ne 0 ]; then
  echo 1>&2
  warn "Filesystem ordering determinism gate FAILED."
  warn "Fix by sorting explicitly (e.g., 'sorted(...)', '.sort()', '... | sort'),"
  warn "or add waiver only if ordering provably does not matter:"
  warn "  # SV_ALLOW_UNSORTED_FS_ORDER"
  exit 1
fi

say "OK: filesystem ordering determinism gate passed."
"""

def main():
  if not CHECK.exists():
    raise SystemExit(f"ERROR: missing {CHECK}")
  cur = CHECK.read_text()
  if cur == NEW:
    print(f"OK: unchanged {CHECK}")
    return
  CHECK.write_text(NEW)
  os.chmod(CHECK, 0o755)
  print(f"OK: wrote {CHECK}")

if __name__ == "__main__":
  main()
