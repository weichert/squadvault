from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "scripts" / "prove_ci.sh"

NEW_LINE = "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh\n"
EXACTNESS = "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\n"
PARITY = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"

def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)

def main() -> int:
    text = TARGET.read_text(encoding="utf-8")

    canonical_block = EXACTNESS + PARITY + NEW_LINE
    old_block = EXACTNESS + NEW_LINE + PARITY

    if canonical_block in text:
        print("OK: prove_ci already contains registry completeness gate in canonical sorted order (noop)")
        return 0

    if old_block in text:
        text = text.replace(old_block, canonical_block, 1)
        TARGET.write_text(text, encoding="utf-8")
        print("OK: reordered registry completeness gate into canonical sorted order")
        return 0

    if EXACTNESS not in text:
        die("ERROR: exactness gate anchor not found in scripts/prove_ci.sh")
    if PARITY not in text:
        die("ERROR: parity gate anchor not found in scripts/prove_ci.sh")

    exact_idx = text.index(EXACTNESS)
    parity_idx = text.index(PARITY)
    if parity_idx < exact_idx:
        die("ERROR: parity gate appears before exactness gate; refusing unexpected prove_ci shape")

    if NEW_LINE in text:
        die("ERROR: registry completeness gate exists but not in expected local block shape")

    expected_block = EXACTNESS + PARITY
    if expected_block not in text:
        die("ERROR: exactness/parity adjacency block not found; refusing unexpected prove_ci shape")

    text = text.replace(expected_block, canonical_block, 1)
    TARGET.write_text(text, encoding="utf-8")
    print("OK: added registry completeness gate to scripts/prove_ci.sh in canonical sorted order")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
