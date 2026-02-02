from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")

NEEDLE_LINE = "scripts/_patch_add_golden_path_production_freeze_v1.py\n"

ANCHOR = "# Canonical ops patchers (allowlist)\n"
AUTO_END = "# === /SquadVault: track canonical ops patchers (auto) ===\n"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    txt = TARGET.read_text(encoding="utf-8")

    # Ensure the file contains the auto allowlist region end marker.
    if AUTO_END not in txt:
        raise SystemExit("ERROR: could not locate canonical allowlist end marker in .gitignore")

    # 1) Remove the fallback mini-block we just appended at EOF (if present).
    # It should look exactly like:
    #   \n# Canonical ops patchers (allowlist)\n
    #   scripts/_patch_add_golden_path_production_freeze_v1.py\n
    fallback_block = "\n# Canonical ops patchers (allowlist)\n" + NEEDLE_LINE
    txt2 = txt.replace(fallback_block, "\n")

    # 2) If the needle is already present somewhere else, don't duplicate.
    if NEEDLE_LINE in txt2:
        TARGET.write_text(txt2, encoding="utf-8")
        print("OK: removed fallback block; needle already present elsewhere")
        return

    # 3) Insert needle into the canonical block immediately before AUTO_END.
    # Prefer inserting after ANCHOR if we can find it before AUTO_END.
    pre, post = txt2.split(AUTO_END, 1)

    if ANCHOR in pre:
        # Insert after the anchor line (and keep rest of block intact).
        head, rest = pre.split(ANCHOR, 1)
        pre2 = head + ANCHOR + NEEDLE_LINE + rest
    else:
        # If anchor missing, insert at end of the prelude (still before AUTO_END).
        if not pre.endswith("\n"):
            pre += "\n"
        pre2 = pre + NEEDLE_LINE

    out = pre2 + AUTO_END + post
    TARGET.write_text(out, encoding="utf-8")
    print("OK: inserted needle into canonical allowlist block and removed fallback")

if __name__ == "__main__":
    main()
