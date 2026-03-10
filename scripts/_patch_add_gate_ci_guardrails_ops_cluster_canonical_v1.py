from __future__ import annotations

from pathlib import Path
import stat

REPO = Path(__file__).resolve().parents[1]
PROVE_CI = REPO / "scripts" / "prove_ci.sh"
TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
GATE = REPO / "scripts" / "gate_ci_guardrails_ops_cluster_canonical_v1.sh"

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 - <<'PY_CHECK'
from pathlib import Path

prove = Path("scripts/prove_ci.sh")
text = prove.read_text(encoding="utf-8")

expected_lines = [
    "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
    "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
]

lines = text.splitlines()
positions = {}
for idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped in expected_lines:
        if stripped in positions:
            raise SystemExit(f"ERROR: duplicate Ops guardrails cluster line found: {stripped}")
        positions[stripped] = idx

missing = [line for line in expected_lines if line not in positions]
if missing:
    raise SystemExit(
        "ERROR: missing Ops guardrails cluster line(s) in scripts/prove_ci.sh:\\n- "
        + "\\n- ".join(missing)
    )

ordered_positions = [positions[line] for line in expected_lines]
start = min(ordered_positions)
end = max(ordered_positions) + 1
actual_block = [lines[i].strip() for i in range(start, end)]

if actual_block != expected_lines:
    raise SystemExit(
        "ERROR: Ops guardrails cluster in scripts/prove_ci.sh is not canonical.\\n\\n"
        "Expected block:\\n- " + "\\n- ".join(expected_lines) + "\\n\\n"
        "Actual block:\\n- " + "\\n- ".join(actual_block)
    )

print("OK: CI Guardrails Ops cluster canonical (v1)")
PY_CHECK
"""

GATE_LINE = "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh\n"
TSV_LINE = "scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh\tOps guardrails cluster canonical gate (v1)\n"
TSV_ANCHOR = "scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh\tOps guardrails entrypoint renderer shape gate (v1)\n"

def write_if_changed(path: Path, text: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True

def ensure_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def canonicalize_prove_ci(text: str) -> str:
    required = [
        GATE_LINE,
        "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\n",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh\n",
        "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh\n",
        "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh\n",
    ]

    missing = [line.strip() for line in required if line not in text]
    if missing and missing != [GATE_LINE.strip()]:
        raise SystemExit(
            "ERROR: missing required Ops guardrails line(s) in scripts/prove_ci.sh:\\n- "
            + "\\n- ".join(missing)
        )

    if GATE_LINE not in text:
        anchor = "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\n"
        if anchor not in text:
            raise SystemExit(
                "ERROR: could not find Ops cluster insertion anchor in scripts/prove_ci.sh"
            )
        text = text.replace(anchor, GATE_LINE + anchor, 1)

    lines = text.splitlines(keepends=True)
    target_set = set(required)
    positions = [i for i, line in enumerate(lines) if line in target_set]
    extracted = [lines[i] for i in positions]

    if len(extracted) != len(required):
        raise SystemExit(
            "ERROR: expected exactly one occurrence of each Ops cluster line in scripts/prove_ci.sh"
        )

    if set(extracted) != target_set:
        raise SystemExit("ERROR: extracted Ops cluster lines do not match expected set")

    start = min(positions)
    end = max(positions) + 1
    new_lines = lines[:start] + required + lines[end:]
    return "".join(new_lines)

def patch_tsv(text: str) -> str:
    if TSV_LINE in text:
        return text
    if TSV_ANCHOR not in text:
        raise SystemExit(
            "ERROR: could not find TSV anchor for cluster canonical gate"
        )
    return text.replace(TSV_ANCHOR, TSV_ANCHOR + TSV_LINE, 1)

def main() -> int:
    changed = False

    if write_if_changed(GATE, GATE_TEXT):
        ensure_executable(GATE)
        changed = True
    else:
        ensure_executable(GATE)

    prove_text = PROVE_CI.read_text(encoding="utf-8")
    new_prove_text = canonicalize_prove_ci(prove_text)
    if new_prove_text != prove_text:
        PROVE_CI.write_text(new_prove_text, encoding="utf-8")
        changed = True

    tsv_text = TSV.read_text(encoding="utf-8")
    new_tsv_text = patch_tsv(tsv_text)
    if new_tsv_text != tsv_text:
        TSV.write_text(new_tsv_text, encoding="utf-8")
        changed = True

    if changed:
        print("OK: added CI Guardrails Ops cluster canonical gate (v1)")
    else:
        print("OK: CI Guardrails Ops cluster canonical gate already present (noop)")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
