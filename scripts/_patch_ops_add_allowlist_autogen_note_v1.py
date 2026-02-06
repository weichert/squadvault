from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_pair_allowlist_v1.txt")

NOTE_LINE = (
    "# NOTE: This file is auto-rewritten by "
    "scripts/patch_ops_rewrite_patch_pair_allowlist_v2.sh\n"
)


def main() -> int:
    text = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)

    # If note already present, do nothing
    if any(NOTE_LINE.strip() == line.strip() for line in text):
        print("OK: allowlist autogen note already present")
        return 0

    out: list[str] = []
    inserted = False

    for line in text:
        out.append(line)
        # Insert note after the rule block header
        if not inserted and line.startswith("# One path per line"):
            out.append(NOTE_LINE)
            inserted = True

    if not inserted:
        raise RuntimeError("Failed to find insertion point in allowlist header")

    TARGET.write_text("".join(out), encoding="utf-8")
    print("OK: added autogen note to patch_pair_allowlist_v1.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
