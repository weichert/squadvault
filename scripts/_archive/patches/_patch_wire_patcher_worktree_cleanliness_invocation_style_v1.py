from __future__ import annotations

from pathlib import Path

WIRE = Path("scripts/_patch_prove_ci_wire_worktree_cleanliness_gate_v1.py")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not WIRE.exists():
        die(f"missing {WIRE}")

    text = WIRE.read_text(encoding="utf-8")

    old = "bash scripts/gate_worktree_cleanliness_v1.sh"
    new = "scripts/gate_worktree_cleanliness_v1.sh"

    if old not in text:
        return

    WIRE.write_text(text.replace(old, new), encoding="utf-8")

if __name__ == "__main__":
    main()
