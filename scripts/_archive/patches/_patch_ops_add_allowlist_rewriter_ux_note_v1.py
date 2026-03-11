from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh")

UX_NOTE = (
    'echo "NOTE: This script regenerates scripts/patch_pair_allowlist_v1.txt from the patcher/wrapper pairing gate."\n'
    'echo "      Manual edits to the allowlist will be overwritten."\n'
)

INSERT_AFTER = 'echo "=== Patch: ops rewrite patch_pair_allowlist_v1.txt from gate output (v2) ==="\n'


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    if UX_NOTE.strip() in text:
        print("OK: UX note already present in allowlist rewriter wrapper")
        return 0

    if INSERT_AFTER not in text:
        raise RuntimeError("Failed to find insertion anchor in wrapper")

    new_text = text.replace(INSERT_AFTER, INSERT_AFTER + "\n" + UX_NOTE, 1)

    TARGET.write_text(new_text, encoding="utf-8")
    print("OK: added UX note to patch_ops_rewrite_patch_pair_allowlist_v2.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
