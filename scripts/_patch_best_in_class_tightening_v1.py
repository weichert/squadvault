from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "patch_best_in_class_tightening_v1.sh"

def main() -> None:
    if not WRAPPER.exists():
        raise SystemExit(f"ERROR: missing umbrella wrapper: {WRAPPER}")
    # Intentionally no-op: pairing gate requires a counterpart path.
    # The umbrella wrapper does the real work.
    print("OK: pairing counterpart present (no-op patcher).")

if __name__ == "__main__":
    main()
