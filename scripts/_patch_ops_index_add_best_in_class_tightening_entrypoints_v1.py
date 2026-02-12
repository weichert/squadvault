from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

LINES = [
    "- scripts/gate_ci_runtime_envelope_v1.sh — CI runtime envelope: budget + proof-count drift guard (v1)\n",
    "- scripts/gate_contract_surface_manifest_hash_v1.sh — Contracts: manifest hash exactness gate (v1)\n",
    "- scripts/gate_creative_surface_fingerprint_v1.sh — Creative surface fingerprint canonical gate (v1)\n",
    "- scripts/gate_meta_surface_parity_v1.sh — Meta: surface parity aggregator gate (v1)\n",
]

def main() -> None:
    text = DOC.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: expected bounded markers not found; refusing to patch.")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    if not mid.endswith("\n"):
        mid += "\n"

    changed = False
    for line in LINES:
        if line.strip() in mid:
            continue
        mid += line
        changed = True

    if not changed:
        print("OK: entrypoints already present (idempotent).")
        return

    DOC.write_text(pre + BEGIN + mid + END + post, encoding="utf-8")
    print("OK: added best-in-class tightening entrypoints to Ops guardrails index.")

if __name__ == "__main__":
    main()
