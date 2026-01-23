from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "patch_writing_room_intake_exclusions_v1.sh"

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    needle = "pytest -q"
    if needle not in s:
        raise SystemExit("ERROR: expected 'pytest -q' not found; refusing to patch.")

    replacement = 'PYTHONPATH=".:src${PYTHONPATH:+:$PYTHONPATH}" pytest -q'
    s2 = s.replace(needle, replacement, 1)

    if s2 == s:
        raise SystemExit("ERROR: patch made no changes; refusing to proceed.")

    TARGET.write_text(s2, encoding="utf-8")
    print(f"OK: patched {TARGET.relative_to(ROOT)}")
    print("Next: ./scripts/patch_writing_room_intake_exclusions_v1.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
