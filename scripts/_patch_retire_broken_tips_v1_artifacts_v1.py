from __future__ import annotations

from pathlib import Path

ARTIFACTS = [
    Path("scripts/_patch_prove_ci_idempotence_failure_tips_v1.py"),
    Path("scripts/patch_prove_ci_idempotence_failure_tips_v1.sh"),
]

def main() -> None:
    removed = False
    for p in ARTIFACTS:
        if p.exists():
            p.unlink()
            print(f"OK: removed {p}")
            removed = True
    if not removed:
        print("OK: v1 tips artifacts already absent.")
