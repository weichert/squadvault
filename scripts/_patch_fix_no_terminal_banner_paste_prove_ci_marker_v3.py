from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/prove_ci.sh")

OLD = "==> Gate: no pasted terminal banners in scripts/"
NEW = 'echo "==> Gate: no pasted terminal banners in scripts/"'

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"REFUSE: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")
    if OLD not in src:
        # If it was already fixed manually or by another patch, be idempotent.
        if NEW in src:
            return 0
        raise SystemExit(f"REFUSE: expected marker not found: {OLD}")

    dst = src.replace(OLD, NEW)
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
