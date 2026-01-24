"""DEPRECATED (Ops)
This patcher was used to retrofit scripts/run_week6_writing_room_gate.sh to use shims.

As of:
- scripts/run_week6_writing_room_gate.sh delegates to scripts/run_writing_room_gate_v1.sh
- scripts/run_writing_room_gate_v1.sh is the canonical Writing Room gate

Do not use this patcher. It is retained only for historical reference.
"""
import sys
print("DEPRECATED: do not run this patcher. Use scripts/run_writing_room_gate_v1.sh (canonical).", file=sys.stderr)
raise SystemExit(2)

from pathlib import Path

p = Path("scripts/run_week6_writing_room_gate.sh")
s = p.read_text(encoding="utf-8")

# Guardrails: ensure expected anchors exist (refuse to patch if drift)
needles = [
    "PYTHONPATH=src python -m unittest -v",
    "./scripts/recap.py check \\",
    "./scripts/recap.py golden-path \\",
]
for n in needles:
    if n not in s:
        raise SystemExit(f"ERROR: expected anchor not found: {n!r}. Refusing to patch.")

s2 = s

# 1) Unit tests: use scripts/py wrapper
s2 = s2.replace(
    "PYTHONPATH=src python -m unittest -v",
    "./scripts/py -m unittest -v",
    1,
)

# 2) recap.py -> recap.sh for check + golden-path
s2 = s2.replace("./scripts/recap.py check \\", "./scripts/recap.sh check \\", 1)
s2 = s2.replace("./scripts/recap.py golden-path \\", "./scripts/recap.sh golden-path \\", 1)

if s2 == s:
    raise SystemExit("ERROR: no changes applied (unexpected). Refusing.")

p.write_text(s2, encoding="utf-8")
print("OK: patched scripts/run_week6_writing_room_gate.sh to use ./scripts/py and ./scripts/recap.sh")
