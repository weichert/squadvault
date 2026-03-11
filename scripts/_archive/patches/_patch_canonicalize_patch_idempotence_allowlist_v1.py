from __future__ import annotations

from pathlib import Path
import sys

ALLOWLIST = Path("scripts/patch_idempotence_allowlist_v1.txt")

def norm_lines(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s)
    # stable canonical order + unique
    out = sorted(set(out))
    return out

def main() -> int:
    if not ALLOWLIST.exists():
        raise SystemExit(f"REFUSE: missing allowlist: {ALLOWLIST}")

    src = ALLOWLIST.read_text(encoding="utf-8")
    lines = norm_lines(src)

    header = "# SquadVault — idempotence allowlist (v1)\n# One wrapper path per line. Comments (#) and blank lines ignored.\n\n"
    new_text = header + "\n".join(lines) + ("\n" if lines else "")

    if src == new_text:
        return 0

    ALLOWLIST.write_text(new_text, encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
