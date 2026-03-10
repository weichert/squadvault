from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

EXACT = "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\n"
PARITY = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"
REGISTRY = "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh\n"
SECTION = "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh\n"
RENDER = "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh\n"

TARGETS = [EXACT, PARITY, REGISTRY, SECTION, RENDER]
CANONICAL_BLOCK = "".join(TARGETS)

def main() -> int:
    text = PROVE.read_text(encoding="utf-8")

    missing = [line.strip() for line in TARGETS if line not in text]
    if missing:
        raise SystemExit(
            "ERROR: missing required gate line(s) in scripts/prove_ci.sh:\n- "
            + "\n- ".join(missing)
        )

    if CANONICAL_BLOCK in text:
        print("OK: renderer shape gate canonical slot already satisfied (noop)")
        return 0

    lines = text.splitlines(keepends=True)

    positions = [i for i, line in enumerate(lines) if line in set(TARGETS)]
    extracted = [lines[i] for i in positions]

    if len(extracted) != 5:
        raise SystemExit(
            "ERROR: expected exactly one occurrence of each Ops gate line in scripts/prove_ci.sh"
        )

    if set(extracted) != set(TARGETS):
        raise SystemExit("ERROR: extracted Ops gate lines do not match expected set")

    start = min(positions)
    end = max(positions) + 1

    new_lines = lines[:start] + TARGETS + lines[end:]
    new_text = "".join(new_lines)

    if CANONICAL_BLOCK not in new_text:
        raise SystemExit("ERROR: failed to place Ops gate block into canonical order")

    PROVE.write_text(new_text, encoding="utf-8")
    print("OK: canonicalized Ops renderer shape gate slot in scripts/prove_ci.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
