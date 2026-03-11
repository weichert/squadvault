from __future__ import annotations

from pathlib import Path

TARGETS = [
    Path("scripts/generate_rivalry_chronicle_v1.sh"),
    Path("scripts/persist_rivalry_chronicle_v1.sh"),
    Path("scripts/rivalry_chronicle_generate_v1.sh"),
]

PREFIX = "# SV_CONTRACT_NAME:"

def norm(s: str) -> str:
    return s.replace("\r\n", "\n")

def patch_one(p: Path) -> bool:
    s0 = norm(p.read_text(encoding="utf-8"))
    lines = s0.splitlines(True)

    new_lines: list[str] = []
    removed = False
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.rstrip("\n").startswith(PREFIX):
            removed = True
            # Also drop ONE immediate blank line after the marker (common style).
            i += 1
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            continue
        new_lines.append(ln)
        i += 1

    s1 = "".join(new_lines)
    if s1 != s0:
        p.write_text(s1, encoding="utf-8")
        return True
    return removed  # treat "found but already removed" as False; fine.

def main() -> None:
    changed = 0
    for p in TARGETS:
        if not p.exists():
            raise SystemExit(f"ERROR: expected {p} to exist")
        if patch_one(p):
            changed += 1
    print(f"OK: stripped non-enforcement SV_CONTRACT_NAME markers in {changed} file(s)")

if __name__ == "__main__":
    main()
