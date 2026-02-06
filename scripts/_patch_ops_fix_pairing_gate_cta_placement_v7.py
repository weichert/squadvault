from __future__ import annotations

from pathlib import Path
import runpy

# Pairing gate requires a _patch_*.py counterpart for scripts/patch_*.sh wrappers.
# v7 is wrapper-only (smoke-check improvements), so we delegate to the canonical v6 patcher.

DELEGATE = Path("scripts/_patch_ops_fix_pairing_gate_cta_placement_v6.py")

def main() -> int:
    if not DELEGATE.exists():
        raise FileNotFoundError(f"Missing delegate patcher: {DELEGATE}")

    runpy.run_path(str(DELEGATE), run_name="__main__")
    print("OK: v7 patcher delegated to v6 patcher")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
