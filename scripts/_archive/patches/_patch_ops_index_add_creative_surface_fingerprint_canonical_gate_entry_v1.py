from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

NEEDLE = "- scripts/gate_creative_surface_fingerprint_v1.sh — Creative surface fingerprint canonical gate (v1)"
INSERT = (
    "<!-- SV_CI_GUARDRAIL_GATE_CREATIVE_SURFACE_FINGERPRINT_CANONICAL_v1_BEGIN -->\n"
    "- scripts/gate_creative_surface_fingerprint_canonical_v1.sh — Enforce creative surface fingerprint artifact canonical (v1)\n"
    "<!-- SV_CI_GUARDRAIL_GATE_CREATIVE_SURFACE_FINGERPRINT_CANONICAL_v1_END -->"
)

def main() -> None:
    src = TARGET.read_text(encoding="utf-8")

    if "gate_creative_surface_fingerprint_canonical_v1.sh" in src:
        print("OK: Ops index already contains creative surface fingerprint canonical gate entry (noop).")
        return

    if NEEDLE not in src:
        raise SystemExit(
            "REFUSE: could not find expected Ops index anchor line:\n"
            f"  {NEEDLE}\n"
            "Re-run:\n"
            "  grep -n \"gate_creative_surface_fingerprint_v1.sh\" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
        )

    out = src.replace(NEEDLE, NEEDLE + "\n" + INSERT, 1)

    CANONICAL = out  # canonical rewrite sentinel
    if CANONICAL == src:
        print("OK: Ops index patch produced identical content (noop).")
        return

    TARGET.write_text(CANONICAL, encoding="utf-8")
    print("OK: patched CI_Guardrails_Index_v1.0.md (added canonical gate discoverability entry).")

if __name__ == "__main__":
    main()
