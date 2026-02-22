from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

PLACEHOLDER = "— (autofill) describe gate purpose"

# Canonical, stable, short descriptions (Ops-friendly).
DESC: dict[str, str] = {    "scripts/gate_creative_surface_registry_parity_v1.sh": "Creative Surface Registry parity gate (v1)",
"scripts/gate_proof_surface_registry_excludes_gates_v1.sh": "Gate vs proof boundary: enforce Proof Surface Registry excludes scripts/gate_*.sh (v1)",
    "scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh": "Enforce bounded Ops guardrails entrypoints section + TOC completeness (v2)",
    "scripts/gate_ci_proof_surface_registry_exactness_v1.sh": "CI Proof Surface Registry exactness: enforce machine-managed list matches tracked scripts/prove_*.sh (v1)",
    "scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh": "Prove Ops index contains proof-surface registry discoverability marker + bullet (v1)",
    "scripts/gate_ci_registry_execution_alignment_v1.sh": "Enforce CI proof registry ↔ prove_ci execution alignment (v1)",
    "scripts/gate_contracts_index_discoverability_v1.sh": "Enforce docs/contracts/README.md indexes all versioned contracts (v1)",
    "scripts/gate_docs_integrity_v2.sh": "Docs integrity gate: enforce canonical docs invariants (v2)",
    "scripts/gate_docs_mutation_guardrail_v2.sh": "Guardrail: proofs must not mutate docs unexpectedly (v2)",
    "scripts/gate_enforce_test_db_routing_v1.sh": "Enforce CI uses temp working DB copy (fixture immutable) (v1)",
    "scripts/gate_no_bare_chevron_markers_v1.sh": "Disallow bare '==>' marker lines in scripts/*.sh (v1)",
    "scripts/gate_no_double_scripts_prefix_v2.sh": "Disallow 'scripts/scripts/' path invocations (v2)",
    "scripts/gate_no_obsolete_allowlist_rewrite_artifacts_v1.sh": "Reject obsolete allowlist rewrite recovery artifacts (v1)",
    "scripts/gate_no_terminal_banner_paste_v1.sh": "Detect pasted terminal banner content in scripts/ (v1)",
    "scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh": "Enforce patch-wrapper allowlist is canonical + safe (v1)",
    "scripts/gate_proof_suite_completeness_v1.sh": "Enforce proof runners match registry exactly (v1)",
    "scripts/gate_rivalry_chronicle_output_contract_v1.sh": "Enforce Rivalry Chronicle export conforms to output contract (v1)",

}

def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"ERROR: missing {INDEX}")

    text = INDEX.read_text(encoding="utf-8")

    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: bounded entrypoints markers missing; refuse")

    pre, rest = text.split(BEGIN, 1)
    bounded, post = rest.split(END, 1)

    lines = bounded.splitlines(True)  # keep newlines
    out: list[str] = []
    changed = 0
    unknown: list[str] = []

    for line in lines:
        if PLACEHOLDER in line and line.lstrip().startswith("- scripts/"):
            # Expect shape: "- <path> — (autofill) describe gate purpose"
            parts = line.split()
            # parts[0] == "-" ; parts[1] == "scripts/..."
            if len(parts) < 2:
                out.append(line)
                continue
            path = parts[1].strip()
            desc = DESC.get(path)
            if not desc:
                unknown.append(path)
                out.append(line)
                continue

            # Replace only the placeholder, preserve the rest of the line structure.
            new_line = line.replace(PLACEHOLDER, f"— {desc}")
            out.append(new_line)
            if new_line != line:
                changed += 1
        else:
            out.append(line)

    if unknown:
        raise SystemExit(
            "ERROR: found autofill bullets for unknown paths (add to DESC map):\n  - "
            + "\n  - ".join(sorted(set(unknown)))
        )

    bounded_out = "".join(out)

    # Fail-closed: no placeholders allowed to remain anywhere in bounded section.
    if PLACEHOLDER in bounded_out:
        raise SystemExit("ERROR: autofill placeholder still present after patch; refuse")

    new_text = pre + BEGIN + bounded_out + END + post

    if new_text == text:
        print("OK: no changes needed (autofill already replaced)")
        return

    INDEX.write_text(new_text, encoding="utf-8")
    print("UPDATED:", INDEX)
    print(f"Replaced {changed} autofill bullets")

if __name__ == "__main__":
    main()
