from __future__ import annotations

from pathlib import Path

# Only remove known-bad / superseded artifacts that should not be committed.
# Keep v3+ marker patchers (they are the real patch history), and keep all currently-used wrappers.
REMOVE = [
    Path("scripts/_patch_check_ci_proof_surface_parser_markers_v1.py"),
    Path("scripts/patch_check_ci_proof_surface_parser_markers_v1.sh"),
    Path("scripts/_patch_check_ci_proof_surface_parser_markers_v2.py"),
    Path("scripts/patch_check_ci_proof_surface_parser_markers_v2.sh"),
    Path("scripts/_patch_prove_ci_idempotence_failure_tips_v1.py"),
    Path("scripts/patch_prove_ci_idempotence_failure_tips_v1.sh"),
]

def main() -> None:
    removed = False
    for p in REMOVE:
        if p.exists():
            p.unlink()
            print(f"OK: removed {p}")
            removed = True
    if not removed:
        print("OK: no leftovers to remove (v1).")

if __name__ == "__main__":
    main()
