from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    REPO_ROOT / "scripts" / "patch_add_coverage_baseline_v1.sh",
    REPO_ROOT / "scripts" / "patch_ops_index_add_best_in_class_guardrails_v1.sh",
    REPO_ROOT / "scripts" / "patch_ops_index_add_standard_show_input_need_coverage_gate_v1.sh",
    REPO_ROOT / "scripts" / "patch_ops_index_dedupe_fixture_immutability_proof_entry_v1.sh",
    REPO_ROOT / "scripts" / "patch_prove_ci_wire_indexed_guardrails_v1.sh",
]

def rewrite(text: str) -> str:
    # Canonical: use scripts/py for both compile and execution.
    text = text.replace("python -m py_compile ", "./scripts/py -m py_compile ")
    text = text.replace("python scripts/_patch_", "./scripts/py scripts/_patch_")
    return text

def main() -> None:
    changed = 0
    for p in TARGETS:
        if not p.exists():
            raise SystemExit(f"ERROR: missing target wrapper: {p}")
        before = p.read_text(encoding="utf-8")
        after = rewrite(before)
        if after != before:
            p.write_text(after, encoding="utf-8")
            changed += 1
    print(f"OK: rewrote_wrappers={changed}/{len(TARGETS)}")

if __name__ == "__main__":
    main()
