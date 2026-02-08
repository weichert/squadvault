#!/usr/bin/env bash
set -euo pipefail

# SquadVault — gate: Proof Surface Registry excludes gates (v1)
#
# Canonical rule:
#   CI gates (scripts/gate_*.sh) are enforcement and MUST NOT appear in the Proof Surface Registry.
#
# This gate fails CI if any scripts/gate_*.sh reference is present in:
#   docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md
#
# CWD independence: resolve repo root from this script's location.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

REG="${REPO_ROOT}/docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
if [[ ! -f "${REG}" ]]; then
  echo "ERROR: missing proof surface registry: ${REG}" >&2
  exit 2
fi

# Reject any reference to gate scripts in the registry.
# Keep this intentionally narrow and high-signal.
if grep -nE 'scripts/gate_[A-Za-z0-9_]+\.sh' "${REG}" >/dev/null; then
  echo "ERROR: Proof Surface Registry must not reference CI gates (scripts/gate_*.sh)." >&2
  echo "Offending lines:" >&2
  grep -nE 'scripts/gate_[A-Za-z0-9_]+\.sh' "${REG}" >&2 || true
  exit 1
fi

exit 0
