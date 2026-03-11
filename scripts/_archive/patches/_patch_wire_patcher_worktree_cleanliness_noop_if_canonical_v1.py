from __future__ import annotations

from pathlib import Path

WIRE = Path("scripts/_patch_prove_ci_wire_worktree_cleanliness_gate_v1.py")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not WIRE.exists():
        die(f"missing {WIRE}")

    text = WIRE.read_text(encoding="utf-8")

    # We want to replace the final unconditional PROVE.write_text("".join(out), ...) with:
    #   new_text = "".join(out)
    #   if new_text == original: return
    #   PROVE.write_text(new_text, ...)
    old = '    PROVE.write_text("".join(out), encoding="utf-8")\n'
    if old not in text:
        # Already patched, or code drifted
        return

    replacement = (
        '    new_text = "".join(out)\n'
        '    if new_text == original:\n'
        '        return\n'
        '    PROVE.write_text(new_text, encoding="utf-8")\n'
    )

    WIRE.write_text(text.replace(old, replacement), encoding="utf-8")

if __name__ == "__main__":
    main()
