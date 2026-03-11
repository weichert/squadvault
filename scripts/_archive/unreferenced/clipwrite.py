from __future__ import annotations

import sys
from pathlib import Path

def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)

def main() -> int:
    if len(sys.argv) != 2:
        die("usage: python scripts/clipwrite.py <path>  (content comes from stdin)")
    p = Path(sys.argv[1])
    content = sys.stdin.read()
    if content == "":
        die("FAIL: empty stdin (refusing to write empty file)")
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text(encoding="utf-8") if p.exists() else None
    if old == content:
        print(f"OK: {p} already canonical (no-op).")
        return 0
    p.write_text(content, encoding="utf-8")
    print(f"OK: wrote {p}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
