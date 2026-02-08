from __future__ import annotations

from pathlib import Path

# Delete obsolete iteration files (v1-v3 awk fix + their allowlist wrappers),
# keeping only the v4 fix which actually patched the gate.

TO_DELETE = [
    # awk portability fix iterations (obsolete)
    "scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v1.py",
    "scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v1.sh",
    "scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v2.py",
    "scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v2.sh",
    "scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v3.py",
    "scripts/patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v3.sh",

    # allowlist iterations for obsolete wrappers (v1-v3)
    "scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v1.py",
    "scripts/patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v2.py",
    "scripts/patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v2.sh",
    "scripts/_patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v3.py",
    "scripts/patch_allowlist_patch_wrapper_fix_awk_portability_ci_guardrails_ops_entrypoint_parity_v3.sh",
]

def main() -> None:
    removed = []
    missing = []
    for rel in TO_DELETE:
        p = Path(rel)
        if p.exists():
            p.unlink()
            removed.append(rel)
        else:
            missing.append(rel)

    # Fail-closed? For cleanup, we tolerate missing (idempotent).
    if removed:
        print("REMOVED:")
        for r in removed:
            print("  -", r)
    else:
        print("OK: nothing to remove (already clean)")

if __name__ == "__main__":
    main()
