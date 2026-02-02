#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs add ops invariants index (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUT="docs/ops/invariants/INDEX_v1.0.md"
mkdir -p "$(dirname "${OUT}")"

cat > "${OUT}" <<'MD'
[SV_CANONICAL_HEADER_V1]
Contract Name: Ops Invariants Index
Version: v1.0
Status: CANONICAL

Defers To:
  - Canonical Operating Constitution (Tier-0)

Default: Any behavior not explicitly permitted by higher authority is forbidden.

—

# Ops Invariants Index (v1.0)

This index lists the canonical operational invariants enforced by CI and/or runtime proof harnesses.

## Invariants

- **ENV Determinism Invariant (v1.0)**  
  `docs/ops/invariants/ENV_Determinism_Invariant_v1.0.md`

- **Filesystem Ordering Determinism Invariant (v1.0)**  
  `docs/ops/invariants/Filesystem_Ordering_Determinism_Invariant_v1.0.md`
MD

echo "OK: wrote ${OUT}"
