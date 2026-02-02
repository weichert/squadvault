from pathlib import Path

TARGETS = [
    Path("scripts/path1_run_week.sh"),
    Path("scripts/prove_golden_path.sh"),
]

def patch_text(s: str) -> str:
    # Prefer shim: scripts/py
    s = s.replace("PYTHONPATH=src python -u ", "./scripts/py -u ")
    s = s.replace("PYTHONPATH=src python ", "./scripts/py ")

    # Prefer shim: scripts/recap.sh
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
