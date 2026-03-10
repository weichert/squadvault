from pathlib import Path
import sys

TARGET = Path("scripts/gate_ci_guardrails_registry_completeness_v1.sh")

old = "grep '^bash scripts/gate_.*\\.sh$' \"$PROVE\""
new = "grep -o 'scripts/gate_[^[:space:]]*\\.sh' \"$PROVE\""

text = TARGET.read_text(encoding="utf-8")

if new in text:
    print("OK: executed detection already canonical (noop)")
    sys.exit(0)

if old not in text:
    print("ERROR: expected executed-detection pattern not found", file=sys.stderr)
    sys.exit(1)

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")
print("OK: registry completeness executed detection normalized")
