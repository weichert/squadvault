from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")

# Keep this exact and specific; only allow this one canonical patcher.
NEEDLE = "scripts/_patch_add_golden_path_production_freeze_v1.py\n"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    txt = TARGET.read_text(encoding="utf-8")

    if NEEDLE in txt:
        print("OK: already allowlisted")
        return

    # Insert into the existing canonical ops patcher allowlist block if present.
    # We look for a stable anchor comment/header.
    anchor = "# Canonical ops patchers (allowlist)\n"
    if anchor in txt:
        parts = txt.split(anchor, 1)
        head, rest = parts[0], parts[1]
        # Insert immediately after the anchor line.
        txt2 = head + anchor + NEEDLE + rest
        TARGET.write_text(txt2, encoding="utf-8")
        print("OK: inserted into canonical ops patcher allowlist block")
        return

    # Fallback: append a tiny allowlist block at EOF (still deterministic, but less ideal).
    txt2 = txt
    if not txt2.endswith("\n"):
        txt2 += "\n"
    txt2 += "\n# Canonical ops patchers (allowlist)\n" + NEEDLE
    TARGET.write_text(txt2, encoding="utf-8")
    print("OK: appended allowlist block at EOF")

if __name__ == "__main__":
    main()
