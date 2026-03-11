from __future__ import annotations

from pathlib import Path

REGISTRY = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

# Preferred ops index targets (we will write to the first existing)
OPS_CANDIDATES = [
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.1.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
]

MARKER = "<!-- GOLDEN_PATH_OUTPUT_CONTRACT_V1_REFS -->"

DOC_REF = "- Golden Path Output Contract (v1): docs/contracts/golden_path_output_contract_v1.md"
GATE_REF = "- Gate: scripts/gate_golden_path_output_contract_v1.sh"

def remove_from_registry() -> bool:
    if not REGISTRY.exists():
        return False

    txt = REGISTRY.read_text(encoding="utf-8")
    lines = txt.splitlines()

    out: list[str] = []
    changed = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Remove our marker block if it exists in registry
        if line.strip() == MARKER:
            changed = True
            # skip marker + subsequent bullets (doc+gate) if present
            i += 1
            while i < len(lines) and lines[i].startswith("- "):
                i += 1
            continue

        # Also remove the specific forbidden gate line if present (even without marker)
        if line.strip() == f"- Gate: scripts/gate_golden_path_output_contract_v1.sh":
            changed = True
            i += 1
            continue

        out.append(line)
        i += 1

    if changed:
        REGISTRY.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")

    return changed

def add_to_ops_index() -> bool:
    target = next((p for p in OPS_CANDIDATES if p.exists()), None)
    if target is None:
        raise SystemExit(
            "No CI Guardrails ops index found (expected CI_Guardrails_Index_v1.0.md or v1.1.md)."
        )

    txt = target.read_text(encoding="utf-8")
    if MARKER in txt:
        return False  # already present

    block = f"\n{MARKER}\n{DOC_REF}\n{GATE_REF}\n"
    target.write_text(txt.rstrip() + block, encoding="utf-8")
    return True

def main() -> None:
    _ = remove_from_registry()
    _ = add_to_ops_index()

if __name__ == "__main__":
    main()
