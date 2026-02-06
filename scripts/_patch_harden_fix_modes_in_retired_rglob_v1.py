from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/_patch_fix_modes_in_retired_v1.py")

OLD = "for p in sorted(RET.iterdir()):"
NEW = "for p in sorted(RET.rglob(\"*\")):"


def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if NEW in txt:
        print("OK: target already uses rglob()")
        return

    if OLD not in txt:
        die("refusing to patch: expected iterdir() loop not found (file changed unexpectedly)")

    TARGET.write_text(txt.replace(OLD, NEW, 1), encoding="utf-8")
    print("OK: updated _patch_fix_modes_in_retired_v1.py to recurse via rglob()")


if __name__ == "__main__":
    main()
