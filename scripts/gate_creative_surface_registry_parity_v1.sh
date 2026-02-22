#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

REG="docs/80_indices/ops/Creative_Surface_Registry_v1.0.md"

if test ! -f "$REG"; then
  echo "ERROR: missing creative surface registry doc: $REG" >&2
  exit 2
fi

# Parse registry lines of the form:
# - **Fingerprint generator**: `path`
# - **Canonical fingerprint artifact**: `path`
# - **Canonical gate**: `path`
# - **Related contract**: `path`
gen="$(grep -n --fixed-string "**Fingerprint generator**" "$REG" | head -n 1 | sed -E 's/.*`([^`]+)`.*/\1/' || true)"
artifact="$(grep -n --fixed-string "**Canonical fingerprint artifact**" "$REG" | head -n 1 | sed -E 's/.*`([^`]+)`.*/\1/' || true)"
gate="$(grep -n --fixed-string "**Canonical gate**" "$REG" | head -n 1 | sed -E 's/.*`([^`]+)`.*/\1/' || true)"
contract="$(grep -n --fixed-string "**Related contract**" "$REG" | head -n 1 | sed -E 's/.*`([^`]+)`.*/\1/' || true)"

if test -z "${gen}"; then
  echo "ERROR: registry missing Fingerprint generator line with backticked path" >&2
  exit 2
fi
if test -z "${artifact}"; then
  echo "ERROR: registry missing Canonical fingerprint artifact line with backticked path" >&2
  exit 2
fi
if test -z "${gate}"; then
  echo "ERROR: registry missing Canonical gate line with backticked path" >&2
  exit 2
fi
if test -z "${contract}"; then
  echo "ERROR: registry missing Related contract line with backticked path" >&2
  exit 2
fi

# Existence checks
if test ! -f "$gen"; then
  echo "ERROR: registry generator path does not exist: $gen" >&2
  exit 2
fi
if test ! -f "$gate"; then
  echo "ERROR: registry gate path does not exist: $gate" >&2
  exit 2
fi
if test ! -f "$artifact"; then
  echo "ERROR: registry fingerprint artifact path does not exist: $artifact" >&2
  exit 2
fi
if test ! -f "$contract"; then
  echo "ERROR: registry related contract path does not exist: $contract" >&2
  exit 2
fi

# Canonical expected values (symmetry hardening)
exp_gen="scripts/gen_creative_surface_fingerprint_v1.py"
exp_artifact="artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json"
exp_gate="scripts/gate_creative_surface_fingerprint_canonical_v1.sh"
exp_contract="docs/contracts/creative_sharepack_output_contract_v1.md"

fail=0
if test "$gen" != "$exp_gen"; then
  echo "ERROR: generator mismatch: registry=$gen expected=$exp_gen" >&2
  fail=1
fi
if test "$artifact" != "$exp_artifact"; then
  echo "ERROR: artifact mismatch: registry=$artifact expected=$exp_artifact" >&2
  fail=1
fi
if test "$gate" != "$exp_gate"; then
  echo "ERROR: gate mismatch: registry=$gate expected=$exp_gate" >&2
  fail=1
fi
if test "$contract" != "$exp_contract"; then
  echo "ERROR: contract mismatch: registry=$contract expected=$exp_contract" >&2
  fail=1
fi

if test "$fail" -ne 0; then
  exit 2
fi

echo "OK: creative surface registry parity gate passed (v1)"
