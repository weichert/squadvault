from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not PROVE.exists():
        die(f"missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    old = "bash scripts/gate_worktree_cleanliness_v1.sh"
    new = "scripts/gate_worktree_cleanliness_v1.sh"

    if old not in text:
        return

    # Replace ONLY the gate invocations, not any other proof runner lines.
    text2 = text.replace(old, new)

    PROVE.write_text(text2, encoding="utf-8")

if __name__ == "__main__":
    main()
