from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/check_patch_pairs_v1.sh")

CTA_SENTINEL = '=== NEXT: Fix patcher/wrapper pairing failures ==='
FAIL_ANCHOR = 'FAIL: patcher/wrapper pairing gate failed.'
ALLOWLIST_ANCHOR = 'scripts/patch_pair_allowlist_v1.txt'

# IMPORTANT: no rc reference at all (avoids set -u issues)
CTA_ECHO_BLOCK = """\
echo
echo "=== NEXT: Fix patcher/wrapper pairing failures ==="
echo "1) Add the missing pair(s): scripts/patch_*.sh <-> scripts/_patch_*.py"
echo "2) Then regenerate the allowlist (if still needed):"
echo "   bash scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh"
echo "NOTE: scripts/patch_pair_allowlist_v1.txt is auto-generated; manual edits will be overwritten."
echo
"""

def strip_existing_cta(raw: str) -> tuple[str, int]:
    # Remove first if-block containing the CTA sentinel (best-effort, conservative).
    pat = re.compile(
        r'(?ms)^[ \t]*if \[ "\$\{rc\}" -ne 0 \]; then\n.*?'
        + re.escape(CTA_SENTINEL)
        + r'.*?^[ \t]*fi\n'
    )
    return pat.subn("", raw, count=1)

def inject_cta_in_failure_section(raw: str) -> tuple[str, bool]:
    lines = raw.splitlines(keepends=True)

    # Find the FAIL line, then find the first allowlist-path line *after* it,
    # then insert CTA immediately after that allowlist line.
    idx_fail = None
    for i, line in enumerate(lines):
        if FAIL_ANCHOR in line:
            idx_fail = i
            break
    if idx_fail is None:
        return raw, False

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

    # If sentinel exists before FAIL anchor, it's definitely misplaced.
    idx_cta = raw.find(CTA_SENTINEL)
    idx_fail = raw.find(FAIL_ANCHOR)

    stripped, removed = strip_existing_cta(raw)
    raw2 = stripped

    new_raw, ok = inject_cta_in_failure_section(raw2)
    if not ok:
        raise RuntimeError(
            "Failed to place CTA in failure section.\n"
            "Debug commands:\n"
            "  grep -n \"FAIL: patcher/wrapper pairing gate failed\" scripts/check_patch_pairs_v1.sh\n"
            "  grep -n \"patch_pair_allowlist_v1.txt\" scripts/check_patch_pairs_v1.sh\n"
        )

    TARGET.write_text(new_raw, encoding="utf-8")

    note = []
    if removed:
        note.append(f"removed_prior_blocks={removed}")
    if idx_cta != -1 and idx_fail != -1 and idx_cta < idx_fail:
        note.append("prior_cta_was_before_fail=1")

    extra = (" " + " ".join(note)) if note else ""
    print(f"OK: fixed CTA placement (v2).{extra}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
