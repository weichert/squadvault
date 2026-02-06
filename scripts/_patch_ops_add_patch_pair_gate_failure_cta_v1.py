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

def _inject_before_exit_rc(text: str) -> tuple[str, bool]:
    anchors = [
        'exit "$rc"\n',
        'exit "${rc}"\n',
        'exit $rc\n',
        'exit ${rc}\n',
    ]
    for a in anchors:
        idx = text.find(a)
        if idx != -1:
            before = text[:idx]
            after = text[idx:]
            if "=== NEXT: Fix patcher/wrapper pairing failures ===" in before:
                return text, True
            return before + CTA_BLOCK + after, True
    return text, False

def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")

    if "=== NEXT: Fix patcher/wrapper pairing failures ===" in raw:
        print("OK: failure CTA already present")
        return 0

    new_raw, ok = _inject_before_exit_rc(raw)
    if not ok:
        raise RuntimeError(
            "Failed to find an exit anchor (expected: exit \"$rc\" / exit ${rc} / exit $rc). "
            "Open scripts/check_patch_pairs_v1.sh and adjust the patcher anchor."
        )

    TARGET.write_text(new_raw, encoding="utf-8")
    print("OK: injected failure CTA into scripts/check_patch_pairs_v1.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
