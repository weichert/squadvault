from pathlib import Path

p = Path("scripts/_patch_run_week6_writing_room_gate_use_shims.py")
if not p.exists():
    raise SystemExit("ERROR: missing scripts/_patch_run_week6_writing_room_gate_use_shims.py")

s = p.read_text(encoding="utf-8")

# If already deprecated, no-op.
if "DEPRECATED (Ops)" in s and "run_writing_room_gate_v1.sh" in s:
    print("OK: already deprecated")
    raise SystemExit(0)

banner = '''"""DEPRECATED (Ops)
This patcher was used to retrofit scripts/run_week6_writing_room_gate.sh to use shims.

As of:
- scripts/run_week6_writing_room_gate.sh delegates to scripts/run_writing_room_gate_v1.sh
- scripts/run_writing_room_gate_v1.sh is the canonical Writing Room gate

Do not use this patcher. It is retained only for historical reference.
"""
'''

stub = """import sys
print("DEPRECATED: do not run this patcher. Use scripts/run_writing_room_gate_v1.sh (canonical).", file=sys.stderr)
raise SystemExit(2)

"""

lines = s.splitlines(True)
out = []
i = 0
if lines and lines[0].startswith("#!"):
    out.append(lines[0])
    i = 1

out.append(banner)
out.append(stub)
out.extend(lines[i:])

p.write_text("".join(out), encoding="utf-8")
print("OK: deprecated scripts/_patch_run_week6_writing_room_gate_use_shims.py")
