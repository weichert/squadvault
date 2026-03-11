from pathlib import Path

TARGETS = [
    Path("scripts/run_writing_room_gate_v1.sh"),
    Path("scripts/writing_room_export_gate_v1.sh"),
    Path("scripts/writing_room_select_v1.sh"),
]

BLOCK = """\
echo "=== Shim compliance ==="
bash scripts/check_shims_compliance.sh
echo
"""

def already_has(s: str) -> bool:
    return "check_shims_compliance.sh" in s

def patch_one(p: Path) -> bool:
    if not p.exists():
        print(f"SKIP: missing {p}")
        return False

    s = p.read_text(encoding="utf-8")

    if already_has(s):
        print(f"OK: already patched {p}")
        return False

    # Insert after the first "=== ... ===" banner echo, which each gate prints.
    # If not found, insert after the shebang + set -e line(s).
    lines = s.splitlines(True)

    insert_at = None
    for i, line in enumerate(lines):
        if line.strip().startswith('echo "===') and line.strip().endswith('==="'):
            insert_at = i + 1
            break

    if insert_at is None:
        # fallback: after the last 'set -' line near top
        insert_at = 0
        for i, line in enumerate(lines[:20]):
            if line.startswith("set "):
                insert_at = i + 1

    out = "".join(lines[:insert_at]) + BLOCK + "".join(lines[insert_at:])
    p.write_text(out, encoding="utf-8")
    print(f"OK: patched {p}")
    return True

changed = 0
for p in TARGETS:
    if patch_one(p):
        changed += 1

if changed == 0:
    print("OK: nothing to patch")
