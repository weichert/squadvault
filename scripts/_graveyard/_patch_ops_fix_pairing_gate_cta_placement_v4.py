from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_patch_pairs_v1.sh")

FAIL_ANCHOR = 'FAIL: patcher/wrapper pairing gate failed.'
ALLOWLIST_ANCHOR = 'scripts/patch_pair_allowlist_v1.txt'
CTA_LINE = 'echo "=== NEXT: Fix patcher/wrapper pairing failures ==="'

CTA_ECHO_BLOCK_LINES = [
    "echo\n",
    'echo "=== NEXT: Fix patcher/wrapper pairing failures ==="\n',
    'echo "1) Add the missing pair(s): scripts/patch_*.sh <-> scripts/_patch_*.py"\n',
    'echo "2) Then regenerate the allowlist (if still needed):"\n',
    'echo "   bash scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh"\n',
    'echo "NOTE: scripts/patch_pair_allowlist_v1.txt is auto-generated; manual edits will be overwritten."\n',
    "echo\n",
]

def strip_cta_blocks(lines: list[str]) -> tuple[list[str], int]:
    """
    Remove any CTA block(s) by detecting the CTA_LINE and skipping until the next blank-line echo.
    This avoids regex greed and won't eat unrelated lines.
    """
    out: list[str] = []
    i = 0
    removed = 0

    while i < len(lines):
        line = lines[i]

        if CTA_LINE in line:
            removed += 1

            # If there's an immediately preceding `echo` blank line, remove it too (optional cleanup).
            if out and out[-1].strip() == "echo":
                out.pop()

            # Skip forward through the CTA block until we hit a blank-line echo *after* CTA_LINE.
            i += 1
            while i < len(lines):
                if lines[i].strip() == "echo":
                    i += 1
                    break
                i += 1
            continue

        out.append(line)
        i += 1

    return out, removed

def find_fail_and_allowlist(lines: list[str]) -> tuple[int, int] | None:
    idx_fail = -1
    for i, line in enumerate(lines):
        if FAIL_ANCHOR in line:
            idx_fail = i
            break
    if idx_fail == -1:
        return None

    idx_allow = -1
    for j in range(idx_fail, len(lines)):
        if ALLOWLIST_ANCHOR in lines[j]:
            idx_allow = j
            break
    if idx_allow == -1:
        return None

    return idx_fail, idx_allow

def insert_cta_after_allowlist(lines: list[str], idx_allow: int) -> list[str]:
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        if i == idx_allow:
            # Ensure a blank line before CTA for readability if the allowlist line didn't already end with one.
            out.extend(CTA_ECHO_BLOCK_LINES)
    return out

def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)

    # 1) Strip ALL existing CTA blocks
    stripped, removed = strip_cta_blocks(lines)

    # 2) Re-insert exactly once: after allowlist path echo line in FAIL path
    pos = find_fail_and_allowlist(stripped)
    if pos is None:
        raise RuntimeError(
            "Could not locate FAIL anchor and allowlist line in scripts/check_patch_pairs_v1.sh\n"
            "Run:\n"
            "  grep -n \"FAIL: patcher/wrapper pairing gate failed\" scripts/check_patch_pairs_v1.sh\n"
            "  grep -n \"patch_pair_allowlist_v1.txt\" scripts/check_patch_pairs_v1.sh\n"
        )
    _, idx_allow = pos

    new_lines = insert_cta_after_allowlist(stripped, idx_allow)

    # 3) Sanity: exactly one CTA line should remain
    joined = "".join(new_lines)
    count = joined.count(CTA_LINE)
    if count != 1:
        raise RuntimeError(f"Expected exactly 1 CTA sentinel after rewrite, found {count}")

    TARGET.write_text(joined, encoding="utf-8")
    print(f"OK: deduped + placed CTA after allowlist line (v4). removed_blocks={removed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
