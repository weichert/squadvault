from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_patch_pairs_v1.sh")

FAIL_SUBSTR = "FAIL: patcher/wrapper pairing gate failed"
ALLOWLIST_SUBSTR = "patch_pair_allowlist_v1.txt"
CTA_SENTINEL = 'echo "=== NEXT: Fix patcher/wrapper pairing failures ==="'

CTA_ECHO_BLOCK_LINES = [
    "echo\n",
    'echo "=== NEXT: Fix patcher/wrapper pairing failures ==="\n',
    'echo "1) Add the missing pair(s): scripts/patch_*.sh <-> scripts/_patch_*.py"\n',
    'echo "2) Then regenerate the allowlist (if still needed):"\n',
    'echo "   bash scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh"\n',
    'echo "NOTE: scripts/patch_pair_allowlist_v1.txt is auto-generated; manual edits will be overwritten."\n',
    "echo\n",
]


def strip_existing_cta(lines: list[str]) -> tuple[list[str], int]:
    out: list[str] = []
    removed = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        if CTA_SENTINEL in line:
            removed += 1

            # Drop a preceding blank-line echo if present.
            if out and out[-1].strip() == "echo":
                out.pop()

            # Skip forward until we pass the CTA block's trailing blank-line echo.
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
        if FAIL_SUBSTR in line:
            idx_fail = i
            break
    if idx_fail == -1:
        return None

    idx_allow = -1
    for j in range(idx_fail, len(lines)):
        if ALLOWLIST_SUBSTR in lines[j]:
            idx_allow = j
            break
    if idx_allow == -1:
        return None

    return idx_fail, idx_allow


def insert_after(lines: list[str], idx: int, block: list[str]) -> list[str]:
    out: list[str] = []
    for i, line in enumerate(lines):
        out.append(line)
        if i == idx:
            out.extend(block)
    return out


def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)

    stripped, removed = strip_existing_cta(lines)

    pos = find_fail_and_allowlist(stripped)
    if pos is None:
        # Diagnostics without editing file
        fail_hits = [f"{i+1}:{l.rstrip()}" for i, l in enumerate(stripped) if FAIL_SUBSTR in l]
        allow_hits = [f"{i+1}:{l.rstrip()}" for i, l in enumerate(stripped) if ALLOWLIST_SUBSTR in l]
        raise RuntimeError(
            "Could not locate FAIL + allowlist anchors in scripts/check_patch_pairs_v1.sh\n"
            f"FAIL hits ({len(fail_hits)}):\n  " + ("\n  ".join(fail_hits) if fail_hits else "(none)") + "\n"
            f"ALLOWLIST hits ({len(allow_hits)}):\n  " + ("\n  ".join(allow_hits) if allow_hits else "(none)") + "\n"
            "Tip: run:\n"
            "  grep -n \"FAIL: patcher/wrapper pairing gate failed\" scripts/check_patch_pairs_v1.sh\n"
            "  grep -n \"patch_pair_allowlist_v1.txt\" scripts/check_patch_pairs_v1.sh\n"
        )

    _, idx_allow = pos
    new_lines = insert_after(stripped, idx_allow, CTA_ECHO_BLOCK_LINES)

    joined = "".join(new_lines)
    count = joined.count(CTA_SENTINEL)
    if count != 1:
        raise RuntimeError(f"Expected exactly 1 CTA sentinel after rewrite, found {count}")

    TARGET.write_text(joined, encoding="utf-8")
    print(f"OK: deduped + placed CTA after allowlist line (v5). removed_blocks={removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
