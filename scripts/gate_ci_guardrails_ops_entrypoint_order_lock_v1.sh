#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 - <<'PY_CHECK'
from pathlib import Path

TSV = Path("docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv")
PROVE = Path("scripts/prove_ci.sh")
CLUSTER = Path("scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh")

CANONICAL = [
    "scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoint_order_lock_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
    "scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh",
    "scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh",
    "scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
    "scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh",
]


def fail(msg: str) -> None:
    raise SystemExit(msg)


def parse_prove_ops() -> list[str]:
    out = []
    wanted = {f"bash {p}": p for p in CANONICAL}
    for raw in PROVE.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped in wanted:
            out.append(wanted[stripped])
    return out


def parse_cluster_ops() -> list[str]:
    lines = CLUSTER.read_text(encoding="utf-8").splitlines()
    out = []
    in_list = False
    for raw in lines:
        stripped = raw.strip()
        if stripped == "expected_lines = [":
            in_list = True
            continue
        if in_list and stripped == "]":
            break
        if in_list:
            if not stripped.startswith('"bash scripts/') or not stripped.endswith('",'):
                fail(f"ERROR: malformed expected_lines entry: {stripped}")
            out.append(stripped[1:-2][len("bash "):])
    return out


def parse_tsv_presence() -> set[str]:
    out = set()
    for lineno, raw in enumerate(TSV.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        parts = raw.split("\t")
        if len(parts) != 2:
            fail(f"ERROR: malformed TSV row at line {lineno}: {raw}")
        out.add(parts[0].strip())
    return out


prove_ops = parse_prove_ops()
cluster_ops = parse_cluster_ops()
tsv_paths = parse_tsv_presence()

missing = [p for p in CANONICAL if p not in tsv_paths]
if missing:
    fail("ERROR: missing canonical Ops entries in TSV registry:\n- " + "\n- ".join(missing))

if prove_ops != CANONICAL:
    fail(
        "ERROR: scripts/prove_ci.sh Ops cluster order is not canonical.\n\n"
        "Expected:\n- " + "\n- ".join(CANONICAL) + "\n\n"
        "Actual:\n- " + "\n- ".join(prove_ops)
    )

if cluster_ops != CANONICAL:
    fail(
        "ERROR: cluster canonical expected_lines order is not canonical.\n\n"
        "Expected:\n- " + "\n- ".join(CANONICAL) + "\n\n"
        "Actual:\n- " + "\n- ".join(cluster_ops)
    )

print("OK: CI Guardrails Ops entrypoint order lock (v1)")
PY_CHECK
