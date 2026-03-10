from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/gate_ci_guardrails_execution_order_lock_v1.sh")
text = TARGET.read_text(encoding="utf-8")

pattern = re.compile(
    r'EXPECTED = \[\n(?:    ".*",\n)+\]',
    re.M,
)

replacement = """EXPECTED = [
    "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_order_lock_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
    "bash scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh",
    "bash scripts/gate_ci_guardrails_registry_authority_v1.sh",
    "bash scripts/gate_ci_guardrails_registry_completeness_v1.sh",
    "bash scripts/gate_ci_guardrails_execution_order_lock_v1.sh",
    "bash scripts/gate_ci_guardrails_surface_freeze_v1.sh",
]"""

updated, count = pattern.subn(replacement, text, count=1)
if count != 1:
    print("ERROR: could not locate EXPECTED block in execution order lock gate", file=sys.stderr)
    raise SystemExit(1)

if updated == text:
    print("OK: EXPECTED block already canonical (noop)")
    raise SystemExit(0)

TARGET.write_text(updated, encoding="utf-8")
print("OK: updated execution order lock EXPECTED block to canonical repo order")
