from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")
BEGIN = "# SV_PATCH: pinned, git-tracked pytest list (avoid broad `pytest -q Tests`)"
NOTE = "# NOTE: do not replace with `pytest -q Tests`. This block is intentionally pinned."

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    if NOTE in s:
        return

    lines = s.splitlines(True)
    for i, line in enumerate(lines):
        if line.rstrip("\n") == BEGIN:
            lines.insert(i + 1, NOTE + "\n")
            TARGET.write_text("".join(lines), encoding="utf-8")
            return

    raise SystemExit("ERROR: could not find pinned block begin marker; refusing")

if __name__ == "__main__":
    main()
