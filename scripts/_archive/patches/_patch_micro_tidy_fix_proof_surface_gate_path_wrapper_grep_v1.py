from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/patch_fix_ci_proof_surface_registry_gate_path_v1.sh")

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"REFUSE: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    # Replace the "old reference is gone" grep line to exclude this wrapper + its patcher.
    old = "grep -nR --exclude-dir='__pycache__' \"gate_ci_proof_surface_registry_v1.sh\" docs scripts | head -n 50 || true"
    new = (
        "grep -nR --exclude-dir='__pycache__' \\\n"
        "  --exclude='patch_fix_ci_proof_surface_registry_gate_path_v1.sh' \\\n"
        "  --exclude='_patch_fix_ci_proof_surface_registry_gate_path_v1.py' \\\n"
        "  \"gate_ci_proof_surface_registry_v1.sh\" docs scripts | head -n 50 || true"
    )

    if old not in src:
        raise SystemExit("REFUSE: expected grep line not found (wrapper drift); won't patch blindly")

    dst = src.replace(old, new)
    if dst == src:
        return 0

    TARGET.write_text(dst, encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
