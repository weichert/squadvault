from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

PARITY = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"
RENDER = "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh\n"

def main() -> int:
    text = PROVE.read_text(encoding="utf-8")

    if PARITY not in text:
        raise SystemExit("ERROR: parity gate line not found in scripts/prove_ci.sh")
    if RENDER not in text:
        raise SystemExit("ERROR: renderer shape gate line not found in scripts/prove_ci.sh")

    old_pair = RENDER + PARITY
    new_pair = PARITY + RENDER

    if new_pair in text:
        print("OK: renderer shape gate ordering already canonical (noop)")
        return 0

    if old_pair not in text:
        raise SystemExit(
            "ERROR: expected adjacent out-of-order pair not found in scripts/prove_ci.sh"
        )

    text = text.replace(old_pair, new_pair, 1)
    PROVE.write_text(text, encoding="utf-8")
    print("OK: fixed renderer shape gate ordering in scripts/prove_ci.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
