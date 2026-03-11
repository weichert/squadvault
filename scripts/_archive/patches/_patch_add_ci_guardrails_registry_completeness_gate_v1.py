from pathlib import Path
import sys

repo = Path(__file__).resolve().parents[1]
prove = repo / "scripts" / "prove_ci.sh"

gate_line = "bash scripts/gate_ci_guardrails_registry_completeness_v1.sh\n"

text = prove.read_text()

if gate_line in text:
    sys.exit(0)

anchor = "bash scripts/gate_ci_guardrails_registry_authority_v1.sh\n"

if anchor not in text:
    raise SystemExit("anchor not found")

text = text.replace(anchor, anchor + gate_line)

prove.write_text(text)
