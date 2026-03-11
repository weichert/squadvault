from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

SENTINEL = "SV_PATCH: filesystem ordering gate ignores pyc/__pycache__ (v1)"

NOTE_BLOCK = f"""\
<!-- {SENTINEL} -->
### Filesystem Ordering Determinism — Bytecode Exclusion

The filesystem ordering determinism gate intentionally ignores:

- `__pycache__/` directories
- `*.pyc` Python bytecode files

Rationale:
- bytecode is **not** a source-of-truth input
- local `py_compile` runs can embed incidental string fragments
- scanning bytecode creates **false positives** unrelated to real ordering bugs

This exclusion is **narrow**, **portable (BSD/GNU compatible)**, and does **not** weaken
ordering guarantees for tracked source files.
<!-- /{SENTINEL} -->
"""

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if SENTINEL in txt:
        print("OK: CI Guardrails Index already contains pyc exclusion note")
        return

    anchor = "### Filesystem Ordering Determinism Guardrail"
    if anchor not in txt:
        die(f"refusing to patch: anchor not found: {anchor}")

    lines = txt.splitlines(True)
    out: list[str] = []
    inserted = False

    for ln in lines:
        out.append(ln)
        if (not inserted) and ln.rstrip("\n") == anchor:
            out.append("\n")
            out.append(NOTE_BLOCK)
            out.append("\n")
            inserted = True

    if not inserted:
        die("refusing to patch: failed to insert note (unexpected)")

    TARGET.write_text("".join(out), encoding="utf-8")
    print("OK: added canonical note about pyc/__pycache__ exclusion to CI Guardrails Index")

if __name__ == "__main__":
    main()
