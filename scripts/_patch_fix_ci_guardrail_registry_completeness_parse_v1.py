from pathlib import Path
import sys

TARGET = Path("scripts/gate_ci_guardrails_registry_completeness_v1.sh")

old = "grep 'scripts/gate_.*\\.sh' \"$REGISTRY\""
new = "grep -o 'scripts/gate_[^[:space:]]*\\.sh' \"$REGISTRY\""

text = TARGET.read_text()

if old not in text:
    print("ERROR: expected pattern not found", file=sys.stderr)
    sys.exit(1)

text = text.replace(old, new, 1)

TARGET.write_text(text)
print("OK: registry completeness parser normalized")