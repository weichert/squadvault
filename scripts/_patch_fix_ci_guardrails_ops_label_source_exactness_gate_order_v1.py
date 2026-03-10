from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

CLUSTER = "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh\n"
EXACT = "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\n"
LABEL = "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh\n"
PARITY = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"
REGISTRY = "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh\n"
SECTION = "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh\n"
RENDER = "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh\n"

CANONICAL_BLOCK = CLUSTER + EXACT + PARITY + REGISTRY + SECTION + LABEL + RENDER

def main() -> int:
    text = PROVE.read_text(encoding="utf-8")

    required = [CLUSTER, EXACT, PARITY, REGISTRY, SECTION, LABEL, RENDER]
    missing = [line.strip() for line in required if line not in text]
    if missing:
        raise SystemExit(
            "ERROR: missing required gate line(s) in scripts/prove_ci.sh:\n- "
            + "\n- ".join(missing)
        )

    if CANONICAL_BLOCK in text:
        print("OK: ops label source exactness gate ordering already canonical (noop)")
        return 0

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
    new_text = "".join(new_lines)

    if CANONICAL_BLOCK not in new_text:
        raise SystemExit("ERROR: failed to place Ops cluster block into canonical order")

    PROVE.write_text(new_text, encoding="utf-8")
    print("OK: canonicalized ops label source exactness gate order in scripts/prove_ci.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
