from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")

NEEDLE_BAD = "scripts/_patch_add_golden_path_production_freeze_v1.py\n"
NEEDLE_GOOD = "!scripts/_patch_add_golden_path_production_freeze_v1.py\n"

AUTO_END = "# === /SquadVault: track canonical ops patchers (auto) ===\n"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    txt = TARGET.read_text(encoding="utf-8")

    if AUTO_END not in txt:
        raise SystemExit("ERROR: could not locate canonical allowlist end marker in .gitignore")

    # Replace bad with good (most common case).
    txt2 = txt.replace(NEEDLE_BAD, NEEDLE_GOOD)

    # If neither exists, insert good immediately before AUTO_END.
    if NEEDLE_GOOD not in txt2:
        pre, post = txt2.split(AUTO_END, 1)
        if not pre.endswith("\n"):
            pre += "\n"
        pre += NEEDLE_GOOD
        txt2 = pre + AUTO_END + post

    if txt2 == txt:
        print("OK: no changes needed")
        return

    TARGET.write_text(txt2, encoding="utf-8")
    print("OK: fixed allowlist bang for production freeze patcher (v3)")

if __name__ == "__main__":
    main()
