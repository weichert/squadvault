from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/check_patch_pairs_v1.sh")

FAIL_ANCHOR = 'FAIL: patcher/wrapper pairing gate failed.'
ALLOWLIST_ANCHOR = 'scripts/patch_pair_allowlist_v1.txt'
CTA_SENTINEL = '=== NEXT: Fix patcher/wrapper pairing failures ==='

CTA_ECHO_BLOCK = """\
echo
echo "=== NEXT: Fix patcher/wrapper pairing failures ==="
echo "1) Add the missing pair(s): scripts/patch_*.sh <-> scripts/_patch_*.py"
echo "2) Then regenerate the allowlist (if still needed):"
echo "   bash scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh"
echo "NOTE: scripts/patch_pair_allowlist_v1.txt is auto-generated; manual edits will be overwritten."
echo
"""

def strip_all_cta_blocks(raw: str) -> tuple[str, int]:
    # Remove ANY contiguous echo-block that contains the CTA sentinel.
    # This handles both echo-only CTAs and CTAs wrapped in if-blocks.
    pat = re.compile(
        r'(?ms)^(?:[ \t]*(?:if\b.*?then|echo\b.*)\n)*?'
        + re.escape('echo "' + CTA_SENTINEL + '"')
        + r'.*?(?:\n[ \t]*echo\b.*?)*\n'
    )
    new_raw, n = pat.subn("", raw)
    return new_raw, n

def inject_after_allowlist_in_fail_path(raw: str) -> tuple[str, bool]:
    lines = raw.splitlines(keepends=True)

    # Find FAIL line
    idx_fail = None
    for i, line in enumerate(lines):
        if FAIL_ANCHOR in line:
            idx_fail = i
            break
    if idx_fail is None:
        return raw, False

    # Find allowlist path echo line AFTER FAIL
    idx_allow = None
    for j in range(idx_fail, len(lines)):
        if ALLOWLIST_ANCHOR in lines[j]:
            idx_allow = j
            break
    if idx_allow is None:
        return raw, False

    out: list[str] = []
    for k, line in enumerate(lines):
        out.append(line)
        if k == idx_allow:
            out.append(CTA_ECHO_BLOCK)

    return "".join(out), True

def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")

    stripped, removed = strip_all_cta_blocks(raw)
    new_raw, ok = inject_after_allowlist_in_fail_path(stripped)
    if not ok:
        raise RuntimeError(
            "Failed to re-insert CTA after allowlist path in FAIL path.\n"
            "Debug:\n"
            "  grep -n \"FAIL: patcher/wrapper pairing gate failed\" scripts/check_patch_pairs_v1.sh\n"
            "  grep -n \"patch_pair_allowlist_v1.txt\" scripts/check_patch_pairs_v1.sh\n"
        )

    TARGET.write_text(new_raw, encoding="utf-8")
    print(f"OK: deduped + repositioned pairing gate CTA (v3). removed_blocks={removed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
