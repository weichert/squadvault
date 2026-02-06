from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/_patch_ops_rewrite_patch_pair_allowlist_v2.py")

NOTE = "# NOTE: This file is auto-rewritten by scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh"

INSERT_AFTER_PREFIX = "# One path per line, exact match, git-tracked only."


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if NOTE in text:
        print("OK: NOTE already present in rewriter HEADER")
        return 0

    # Minimal, deterministic textual rewrite:
    # Insert the NOTE line into the HEADER triple-quoted string right after the
    # "One path per line..." header line.
    needle = INSERT_AFTER_PREFIX + "\n"
    if needle not in text:
        raise RuntimeError(f"Failed to find insertion anchor: {INSERT_AFTER_PREFIX!r}")

    replacement = needle + NOTE + "\n"

    new_text = text.replace(needle, replacement, 1)

    # Safety: ensure we didn't accidentally add it outside the HEADER block
    if NOTE not in new_text:
        raise RuntimeError("Rewrite failed: NOTE not found after replacement")

    TARGET.write_text(new_text, encoding="utf-8")
    print("OK: injected NOTE into scripts/_patch_ops_rewrite_patch_pair_allowlist_v2.py HEADER (v1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
