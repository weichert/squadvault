from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/_patch_wire_no_terminal_banner_paste_gate_into_prove_ci_v2.py")

OLD = r'SNIP = "\n==> Gate: no pasted terminal banners in scripts/\nbash scripts/gate_no_terminal_banner_paste_v1.sh\n"'
NEW = r"SNIP = '\necho \"==> Gate: no pasted terminal banners in scripts/\"\nbash scripts/gate_no_terminal_banner_paste_v1.sh\n'"

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"REFUSE: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    # idempotent: if already fixed, do nothing
    if "echo \\\"==> Gate: no pasted terminal banners in scripts/\\\"" in src or 'echo "==> Gate: no pasted terminal banners in scripts/"' in src:
        return 0

    if OLD not in src:
        raise SystemExit("REFUSE: expected old SNIP line not found (file may have changed).")

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
