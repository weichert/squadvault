from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/check_patch_pairs_v1.sh")

CTA_SENTINEL = '=== NEXT: Fix patcher/wrapper pairing failures ==='

CTA_BLOCK = """\
if [ "${rc}" -ne 0 ]; then
  echo
  echo "=== NEXT: Fix patcher/wrapper pairing failures ==="
  echo "1) Add the missing pair(s): scripts/patch_*.sh <-> scripts/_patch_*.py"
  echo "2) Then regenerate the allowlist (if still needed):"
  echo "   bash scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh"
  echo "NOTE: scripts/patch_pair_allowlist_v1.txt is auto-generated; manual edits will be overwritten."
  echo
fi
"""

# We want CTA to appear AFTER the allowlist path line prints.
ALLOWLIST_LINE_ANCHOR = "scripts/patch_pair_allowlist_v1.txt"


def strip_existing_cta(raw: str) -> tuple[str, int]:
    # Remove the first if-block that contains CTA_SENTINEL (conservative).
    pat = re.compile(
        r'(?ms)^[ \t]*if \[ "\$\{rc\}" -ne 0 \]; then\n.*?'
        + re.escape(CTA_SENTINEL)
        + r'.*?^[ \t]*fi\n'
    )
    new_raw, n = pat.subn("", raw, count=1)
    return new_raw, n


def inject_after_allowlist_line(raw: str) -> tuple[str, bool]:
    lines = raw.splitlines(keepends=True)
    out: list[str] = []
    inserted = False

    for line in lines:
        out.append(line)
        if (not inserted) and (ALLOWLIST_LINE_ANCHOR in line):
            # Insert CTA immediately after the allowlist line.
            out.append("\n")
            out.append(CTA_BLOCK)
            inserted = True

    return "".join(out), inserted


def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")

    raw2, removed = strip_existing_cta(raw)
    new_raw, inserted = inject_after_allowlist_line(raw2)

    if not inserted:
        raise RuntimeError(
            "Failed to find allowlist path line anchor in scripts/check_patch_pairs_v1.sh.\n"
            "Run: grep -n \"patch_pair_allowlist_v1.txt\" scripts/check_patch_pairs_v1.sh"
        )

    TARGET.write_text(new_raw, encoding="utf-8")
    print(f"OK: repositioned CTA after allowlist path line. removed_prior_blocks={removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
