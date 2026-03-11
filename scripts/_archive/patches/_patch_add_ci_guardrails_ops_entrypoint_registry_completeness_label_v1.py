from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

NEW_ROW = (
    "scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh\t"
    "CI Guardrails Ops Entrypoint Registry Completeness (v1)"
)

def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)

def main() -> int:
    if not TARGET.is_file():
        die(f"ERROR: missing target TSV: {TARGET}")

    lines = TARGET.read_text(encoding="utf-8").splitlines()

    existing_noncomment = [ln for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]
    if not existing_noncomment:
        die("ERROR: label TSV has no non-comment rows; refusing unexpected shape")

    matches = [ln for ln in lines if ln.strip() == NEW_ROW]
    if matches:
        print("OK: registry completeness label row already present (noop)")
        return 0

    conflicting = [
        ln for ln in lines
        if ln.strip().startswith("scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh\t")
        and ln.strip() != NEW_ROW
    ]
    if conflicting:
        die(
            "ERROR: conflicting registry row already exists for "
            "scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh"
        )

    insert_idx = len(lines)
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped > NEW_ROW:
            insert_idx = i
            break

    new_lines = lines[:insert_idx] + [NEW_ROW] + lines[insert_idx:]
    TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("OK: added registry completeness label row to TSV")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
