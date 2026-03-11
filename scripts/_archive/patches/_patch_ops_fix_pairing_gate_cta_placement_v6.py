from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_patch_pairs_v1.sh")

# We will anchor on the FAIL-path guidance line that precedes the allowlist path print.
FIX_GUIDANCE_SUBSTR = "Fix by adding the missing counterpart, or (rarely) allowlist the path:"

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


def insert_cta_after_fix_guidance(lines: list[str]) -> tuple[list[str], bool]:
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if (not inserted) and (FIX_GUIDANCE_SUBSTR in line):
            out.extend(CTA_ECHO_BLOCK_LINES)
            inserted = True
    return out, inserted


def main() -> int:
    raw = TARGET.read_text(encoding="utf-8")
    lines = raw.splitlines(keepends=True)

    stripped, removed = strip_existing_cta(lines)
    new_lines, inserted = insert_cta_after_fix_guidance(stripped)

    if not inserted:
        hits = [f"{i+1}:{l.rstrip()}" for i, l in enumerate(stripped) if FIX_GUIDANCE_SUBSTR in l]
        raise RuntimeError(
            "Could not locate fix-guidance anchor in scripts/check_patch_pairs_v1.sh\n"
            f"Hits ({len(hits)}):\n  " + ("\n  ".join(hits) if hits else "(none)") + "\n"
            "Tip: grep -n \"Fix by adding the missing counterpart\" scripts/check_patch_pairs_v1.sh"
        )

    joined = "".join(new_lines)
    count = joined.count(CTA_SENTINEL)
    if count != 1:
        raise RuntimeError(f"Expected exactly 1 CTA sentinel after rewrite, found {count}")

    TARGET.write_text(joined, encoding="utf-8")
    print(f"OK: deduped + placed CTA after fix-guidance line (v6). removed_blocks={removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
