#!/usr/bin/env python3
from pathlib import Path
import sys

p = Path("scripts/check_golden_path_recap.sh")
s0 = p.read_text(encoding="utf-8")

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

# Idempotency: if already defaulting to recap.py, do nothing.
if 'RECAP_SCRIPT="${SCRIPT_DIR}/recap.py"' in s0 and '(default: ${SCRIPT_DIR}/recap.py)' in s0:
    print("OK: check_golden_path_recap.sh already defaults --recap-script to recap.py; no changes.")
    raise SystemExit(0)

needle_help = '  --recap-script PATH   (default: ${SCRIPT_DIR}/recap.sh)\n'
repl_help   = '  --recap-script PATH   (default: ${SCRIPT_DIR}/recap.py)\n'

needle_var = 'RECAP_SCRIPT="${SCRIPT_DIR}/recap.sh"\n'
repl_var   = 'RECAP_SCRIPT="${SCRIPT_DIR}/recap.py"\n'

if needle_help not in s0:
    die("Expected --recap-script help default to recap.sh not found; refusing to patch.")
if needle_var not in s0:
    die("Expected RECAP_SCRIPT default assignment to recap.sh not found; refusing to patch.")

s1 = s0.replace(needle_help, repl_help, 1).replace(needle_var, repl_var, 1)

# Sanity
if 'RECAP_SCRIPT="${SCRIPT_DIR}/recap.py"' not in s1:
    die("Patch failed to produce recap.py default; refusing.")
if '(default: ${SCRIPT_DIR}/recap.py)' not in s1:
    die("Patch failed to update help default; refusing.")

p.write_text(s1, encoding="utf-8")
print("OK: patched check_golden_path_recap.sh default --recap-script to recap.py (python-safe)")
