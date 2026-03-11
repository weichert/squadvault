from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

NEEDLE = "bash scripts/gate_creative_surface_fingerprint_v1.sh"
INSERT_LINE = "bash scripts/gate_creative_surface_fingerprint_canonical_v1.sh"

def main() -> None:
    src = TARGET.read_text(encoding="utf-8")

    if INSERT_LINE in src:
        print("OK: prove_ci already invokes creative surface fingerprint canonical gate (noop).")
        return

    if NEEDLE not in src:
        raise SystemExit(
            "REFUSE: could not find expected insertion anchor in scripts/prove_ci.sh:\n"
            f"  {NEEDLE}"
        )

    out = src.replace(
        NEEDLE,
        NEEDLE
        + "\n\n# Creative surface fingerprint canonical drift gate (v1)\n"
        + INSERT_LINE,
        1,
    )

    CANONICAL = out  # canonical rewrite sentinel

    if CANONICAL == src:
        print("OK: prove_ci patch produced identical content (noop).")
        return

    TARGET.write_text(CANONICAL, encoding="utf-8")
    print("OK: patched scripts/prove_ci.sh (added creative surface fingerprint canonical gate).")

if __name__ == "__main__":
    main()
