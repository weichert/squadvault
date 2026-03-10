from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "prove_ci.sh"

NEW_LINE = "bash scripts/gate_ci_guardrails_execution_order_lock_v1.sh\n"

ANCHORS = [
    "bash scripts/gate_ci_guardrails_registry_completeness_v1.sh\n",
    "bash scripts/gate_ci_guardrails_registry_authority_v1.sh\n",
]

text = TARGET.read_text(encoding="utf-8")

if NEW_LINE in text:
    print("OK: execution order lock already wired (noop)")
    raise SystemExit(0)

anchor_found = None
for anchor in ANCHORS:
    if anchor in text:
        anchor_found = anchor
        break

if anchor_found is None:
    print("ERROR: no expected anchor found in scripts/prove_ci.sh", file=sys.stderr)
    raise SystemExit(1)

updated = text.replace(anchor_found, anchor_found + NEW_LINE, 1)

if updated == text:
    print("ERROR: failed to update scripts/prove_ci.sh", file=sys.stderr)
    raise SystemExit(1)

TARGET.write_text(updated, encoding="utf-8")
print("OK: wired execution order lock gate into scripts/prove_ci.sh")
