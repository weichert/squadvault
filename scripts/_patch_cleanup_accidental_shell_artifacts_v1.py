from __future__ import annotations

from pathlib import Path

# These showed up in git status as new files due to a broken heredoc / pasted output.
GARBAGE = [
    Path("NEW"),
    Path("OLD"),
    Path("PY=python"),
    Path("SH"),
    Path("cd"),
    Path("echo"),
    Path("fi"),
    Path("if"),
    Path("return"),
    Path("set"),
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
