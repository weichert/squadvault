from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh")

HINT_LINE = (
    'echo "HINT: After fixing patcher/wrapper pairings, re-run this script to regenerate the allowlist."\n'
)

INSERT_AFTER = (
    'echo "      Manual edits to the allowlist will be overwritten."\n'
)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if HINT_LINE.strip() in text:
        print("OK: refresh hint already present in allowlist rewriter wrapper")
        return 0

    if INSERT_AFTER not in text:
        raise RuntimeError("Failed to find insertion anchor for refresh hint")

    new_text = text.replace(INSERT_AFTER, INSERT_AFTER + HINT_LINE, 1)
    TARGET.write_text(new_text, encoding="utf-8")

    print("OK: added allowlist refresh hint to rewriter wrapper")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
