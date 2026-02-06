#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add ENV determinism invariant + index entry (v1, wrapper-only) ==="

# --- Resolve repo root deterministically ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# --- Paths ---
INVARIANT_DIR="docs/ops/invariants"
INVARIANT_FILE="${INVARIANT_DIR}/ENV_Determinism_Invariant_v1.0.md"
INDEX_NAME="CI_Guardrails_Index_v1.0.md"

INDEX_BULLET="- ENV_Determinism_Invariant_v1.0.md — Enforces deterministic locale/time/hash envelope for all CI proofs (export + fail-loud gate in prove_ci.sh)."

# --- Create invariant if missing ---
mkdir -p "${INVARIANT_DIR}"
if [[ ! -f "${INVARIANT_FILE}" ]]; then
  echo "==> Creating invariant: ${INVARIANT_FILE}"
  cat > "${INVARIANT_FILE}" <<'EOF'
[SV_CANONICAL_HEADER_V1]
Invariant Name: ENV_Determinism_Invariant
Version: v1.0
Status: CANONICAL

Defers To:
  - CI_Cleanliness_Invariant_v1.0.md (as applicable)

Applies To:
  - scripts/prove_ci.sh (authoritative CI proof entrypoint)
  - All downstream proof scripts invoked by prove_ci.sh

Default: Any CI proof run outside this envelope is invalid.

—

# ENV_Determinism_Invariant (v1.0)

## Statement
All SquadVault CI proofs MUST execute inside a deterministic environment envelope to prevent nondeterministic output drift caused by locale, timezone, or Python hash variance.

## Required Deterministic Envelope
The following environment variables MUST be set exactly:

- LC_ALL=C
- LANG=C
- TZ=UTC
- PYTHONHASHSEED=0

## Enforcement
- scripts/prove_ci.sh MUST export the required envelope before invoking any proof scripts.
- scripts/prove_ci.sh MUST validate the envelope (gate) and FAIL LOUDLY if any value differs.

## Failure Mode
If any required variable is missing or differs, CI MUST exit non-zero with a clear error stating the expected and observed value.

## Rationale
Locale and timezone can change ordering and formatting behavior across shells and platforms.
Python hash randomization can introduce ordering variance in hash-based containers when relied upon indirectly.
This invariant constrains the execution surface so proofs remain auditable and reproducible.

## Non-Goals
This invariant does not change product logic, selection logic, or narrative logic.
It constrains only the execution environment for proofs.
EOF
else
  echo "==> Invariant already exists: ${INVARIANT_FILE}"
fi

# --- Locate index (must be exactly one) ---
# Bash 3.2 note: avoid mapfile; use a simple array fill.
INDEX_HITS=()
while IFS= read -r p; do
  INDEX_HITS+=("$p")
done < <(find docs -type f -name "${INDEX_NAME}")

if [[ "${#INDEX_HITS[@]}" -eq 0 ]]; then
  echo "ERROR: could not find ${INDEX_NAME} under docs/" >&2
  exit 2
fi

if [[ "${#INDEX_HITS[@]}" -gt 1 ]]; then
  echo "ERROR: multiple ${INDEX_NAME} files found; refusing to guess:" >&2
  for f in "${INDEX_HITS[@]}"; do
    echo "  - ${f}" >&2
  done
  exit 2
fi

INDEX_FILE="${INDEX_HITS[0]}"
echo "==> Using index: ${INDEX_FILE}"

# --- Append index entry if missing ---
if grep -Fq "ENV_Determinism_Invariant_v1.0.md" "${INDEX_FILE}"; then
  echo "==> Index already references invariant"
else
  echo "==> Appending invariant to index"
  printf "\n%s\n" "${INDEX_BULLET}" >> "${INDEX_FILE}"
fi

# --- Sanity ---
bash -n "${BASH_SOURCE[0]}"
echo "OK: ENV determinism invariant patch complete"
