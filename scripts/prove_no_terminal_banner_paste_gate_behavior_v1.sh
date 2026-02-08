#!/usr/bin/env bash
# SquadVault — proof: terminal banner paste gate behavior (v1)
#
# What this proves:
#  1) Strict mode fails when a *tracked* scripts/*.txt contains a real banner line.
#  2) Anchoring prevents false positives from pattern-literal text (e.g., "'^Last login: '").
#  3) Escape hatch SV_ALLOW_TERMINAL_BANNER_PASTE=1 exits 0 and emits WARN.
#
# Determinism:
#  - Requires clean repo at entry.
#  - Temporarily stages a synthetic file, runs gate, then fully cleans up.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: proof requires clean repo (working tree + index)."
  git status --porcelain=v1
  exit 2
fi

TMP="scripts/.sv_tmp_terminal_banner_probe_v1.txt"

cleanup() {
  set +e
  git reset -q -- "${TMP}" >/dev/null 2>&1
  rm -f "${TMP}"
  set -e
}
trap cleanup EXIT

# --- Case 1: strict mode should FAIL on a tracked banner line ---
cat > "${TMP}" <<'EOF'
Last login: Fri Feb  6 23:41:20 on ttys061
EOF

git add "${TMP}"

set +e
out="$(bash scripts/gate_no_terminal_banner_paste_v1.sh 2>&1)"
rc=$?
set -e

if [[ $rc -eq 0 ]]; then
  echo "ERROR: expected gate to fail in strict mode when banner line is present."
  echo "${out}"
  exit 1
fi

git reset -q -- "${TMP}"
rm -f "${TMP}"

# --- Case 2: anchored patterns should NOT match pattern-literal text ---
cat > "${TMP}" <<'EOF'
  '^Last login: '
EOF

git add "${TMP}"

bash scripts/gate_no_terminal_banner_paste_v1.sh

git reset -q -- "${TMP}"
rm -f "${TMP}"

# --- Case 3: escape hatch should WARN + exit 0 ---
set +e
out2="$(SV_ALLOW_TERMINAL_BANNER_PASTE=1 bash scripts/gate_no_terminal_banner_paste_v1.sh 2>&1)"
rc2=$?
set -e

if [[ $rc2 -ne 0 ]]; then
  echo "ERROR: expected escape hatch to exit 0."
  echo "${out2}"
  exit 1
fi

echo "${out2}" | grep -n "WARN:" >/dev/null

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: proof left repo dirty unexpectedly."
  git status --porcelain=v1
  exit 1
fi

echo "OK: terminal banner gate behavior proved (v1)."
