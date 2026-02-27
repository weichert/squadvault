# Creative Surface Registry v1.0

This document is a **machine-indexed registry surface** for the Creative Surface.

<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_BEGIN -->

<!-- SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_BEGIN -->
## Registry Entries (machine-indexed)


- CREATIVE_SURFACE_REGISTRY_V1
- CREATIVE_SURFACE_REGISTRY_V1_EN
- CREATIVE_SURFACE_SCOPE_V1
<!-- SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_END -->

## Canonical Surfaces

- **Fingerprint generator**: `scripts/gen_creative_surface_fingerprint_v1.py`
- **Canonical fingerprint artifact**: `artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json`
- **Canonical gate**: `scripts/gate_creative_surface_fingerprint_canonical_v1.sh`
- **Related contract**: `docs/contracts/creative_sharepack_output_contract_v1.md`

## Scope (authoritative)

The Creative Surface Fingerprint is computed from git-tracked paths, then restricted by an explicit scope allowlist/denylist in:

- `scripts/gen_creative_surface_fingerprint_v1.py` (`SV_CREATIVE_SURFACE_SCOPE_V1`)

<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_END -->
