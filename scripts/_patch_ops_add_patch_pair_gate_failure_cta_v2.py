from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_patch_pairs_v1.sh")

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

ANCHOR = 'OK: patcher/wrapper pairing gate passed.'  # stable, observed in CI output


def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")

    if "=== NEXT: Fix patcher/wrapper pairing failures ===" in raw:
        print("OK: failure CTA already present")
        return 0

    # Find the line that prints the success marker and insert CTA immediately before it.
    lines = raw.splitlines(keepends=True)
    out: list[str] = []
    inserted = False

    for line in lines:
        if (not inserted) and (ANCHOR in line):
            out.append(CTA_BLOCK)
            inserted = True
        out.append(line)

    if not inserted:
        raise RuntimeError(
            f"Failed to find anchor line containing: {ANCHOR!r}\n"
            "Run: grep -n \"patcher/wrapper pairing gate passed\" scripts/check_patch_pairs_v1.sh"
        )

    TARGET.write_text("".join(out), encoding="utf-8")
    print("OK: injected failure CTA into scripts/check_patch_pairs_v1.sh (v2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
