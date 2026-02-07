from __future__ import annotations

from pathlib import Path
import sys

# We discovered the canonical gate script name in docs/scripts is stale:
#   scripts/gate_ci_proof_surface_registry_v1.sh  (does NOT exist)
# The real checker is:
#   scripts/check_ci_proof_surface_matches_registry_v1.sh

OLD = "scripts/gate_ci_proof_surface_registry_v1.sh"
NEW = "scripts/check_ci_proof_surface_matches_registry_v1.sh"

TARGETS = [
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
    Path("scripts/_patch_index_ci_proof_surface_registry_discoverability_v1.py"),
    Path("scripts/_patch_index_ci_proof_surface_registry_discoverability_v2.py"),
    Path("scripts/_patch_fix_ci_proof_surface_registry_index_discoverability_gate_grep_v1.py"),
    Path("scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh"),
    Path("scripts/patch_index_ci_proof_surface_registry_discoverability_v1.sh"),
    Path("scripts/patch_index_ci_proof_surface_registry_discoverability_v2.sh"),
]

def main() -> int:
    changed = 0
    for p in TARGETS:
        if not p.exists():
            raise SystemExit(f"REFUSE: missing expected target: {p}")

        src = p.read_text(encoding="utf-8")
        if OLD not in src:
            # strict: these specific files were reported by grep; we expect the old value
            raise SystemExit(f"REFUSE: expected '{OLD}' not found in: {p}")

        dst = src.replace(OLD, NEW)
        if dst != src:
            p.write_text(dst, encoding="utf-8")
            changed += 1

    print(f"OK: updated {changed} file(s): {OLD} -> {NEW}")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
