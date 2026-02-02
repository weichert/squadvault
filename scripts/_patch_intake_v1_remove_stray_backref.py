from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "intake_v1.py"

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    # Remove lines that are literally "\1" (optionally surrounded by whitespace)
    out = []
    removed = 0
    for ln in lines:
        if ln.strip() == r"\1":
            removed += 1
            continue
        out.append(ln)

    if removed == 0:
        print("OK: no stray \\1 lines found; nothing to patch.")
        return 0

    TARGET.write_text("".join(out), encoding="utf-8")
    print(f"OK: removed {removed} stray '\\\\1' line(s) from {TARGET.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
