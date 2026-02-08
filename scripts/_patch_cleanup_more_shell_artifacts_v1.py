from __future__ import annotations

from pathlib import Path

GARBAGE = [
    Path("bash"),
    Path("py_compile"),
]

def main() -> None:
    removed = 0
    for p in GARBAGE:
        if p.exists():
            p.unlink()
            print("REMOVED:", p)
            removed += 1
    print("DONE: removed =", removed)

if __name__ == "__main__":
    main()
