from pathlib import Path

TARGETS = [
    Path("scripts/_patch_writing_room_signal_grouping_v1.py"),
    Path("scripts/_patch_intake_v1_restore_adapter_gates.py"),
    Path("scripts/recap.py"),
]

def patch_text(s: str) -> str:
    # Replace example invocations shown to operators.
    s = s.replace("PYTHONPATH=src python -c ", "./scripts/py -c ")
    s = s.replace("PYTHONPATH=src python -m py_compile", "./scripts/py -m py_compile")
    s = s.replace("PYTHONPATH=src python -m unittest", "./scripts/py -m unittest")

    # recap.py help text examples
    s = s.replace("./scripts/recap.py ", "./scripts/recap.sh ")

    return s

changed = 0
for p in TARGETS:
    if not p.exists():
        print(f"SKIP: missing {p}")
        continue
    before = p.read_text(encoding="utf-8")
    after = patch_text(before)
    if after != before:
        p.write_text(after, encoding="utf-8")
        changed += 1
        print(f"OK: patched {p}")
    else:
        print(f"OK: no changes needed {p}")

if changed == 0:
    print("OK: nothing to patch")
