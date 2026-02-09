from __future__ import annotations

from pathlib import Path

# Phase A: explicit marker adoption (comment-only; no behavior change)

TARGETS: dict[str, tuple[str, str]] = {
    # CONTRACT_MARKERS
    "scripts/gate_contract_linkage_v1.sh": (
        "CONTRACT_MARKERS",
        "docs/contracts/Contract_Markers_v1.0.md",
    ),
    # GOLDEN_PATH_OUTPUT
    "scripts/gate_golden_path_output_contract_v1.sh": (
        "GOLDEN_PATH_OUTPUT",
        "docs/contracts/golden_path_output_contract_v1.md",
    ),
    "scripts/prove_golden_path.sh": (
        "GOLDEN_PATH_OUTPUT",
        "docs/contracts/golden_path_output_contract_v1.md",
    ),
    "scripts/run_golden_path_v1.sh": (
        "GOLDEN_PATH_OUTPUT",
        "docs/contracts/golden_path_output_contract_v1.md",
    ),
    # RIVALRY_CHRONICLE_OUTPUT
    "scripts/gate_rivalry_chronicle_output_contract_v1.sh": (
        "RIVALRY_CHRONICLE_OUTPUT",
        "docs/contracts/rivalry_chronicle_output_contract_v1.md",
    ),
    "scripts/prove_rivalry_chronicle_end_to_end_v1.sh": (
        "RIVALRY_CHRONICLE_OUTPUT",
        "docs/contracts/rivalry_chronicle_output_contract_v1.md",
    ),
    "scripts/generate_rivalry_chronicle_v1.sh": (
        "RIVALRY_CHRONICLE_OUTPUT",
        "docs/contracts/rivalry_chronicle_output_contract_v1.md",
    ),
    "scripts/rivalry_chronicle_generate_v1.sh": (
        "RIVALRY_CHRONICLE_OUTPUT",
        "docs/contracts/rivalry_chronicle_output_contract_v1.md",
    ),
    "scripts/persist_rivalry_chronicle_v1.sh": (
        "RIVALRY_CHRONICLE_OUTPUT",
        "docs/contracts/rivalry_chronicle_output_contract_v1.md",
    ),
    "scripts/recap_week_fetch_approved.py": (
        "RIVALRY_CHRONICLE_OUTPUT",
        "docs/contracts/rivalry_chronicle_output_contract_v1.md",
    ),
    "scripts/recap_week_approve.py": (
        "RIVALRY_CHRONICLE_OUTPUT",
        "docs/contracts/rivalry_chronicle_output_contract_v1.md",
    ),
}


def _ensure_markers(path: Path, contract_name: str, doc_path: str) -> bool:
    raw = path.read_text(encoding="utf-8")
    if "SV_CONTRACT_NAME:" in raw or "SV_CONTRACT_DOC_PATH:" in raw:
        # If either exists, require both exact lines; otherwise, fail loudly.
        name_line = f"# SV_CONTRACT_NAME: {contract_name}"
        doc_line = f"# SV_CONTRACT_DOC_PATH: {doc_path}"
        has_name = name_line in raw
        has_doc = doc_line in raw
        if has_name and has_doc:
            return False
        raise SystemExit(
            f"Refusing to patch {path}: partial or mismatched contract markers present.\n"
            f"Expected:\n  {name_line}\n  {doc_line}\n"
        )

    name_line = f"# SV_CONTRACT_NAME: {contract_name}\n"
    doc_line = f"# SV_CONTRACT_DOC_PATH: {doc_path}\n"
    block = name_line + doc_line + "\n"

    lines = raw.splitlines(True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1

    new_lines = lines[:insert_at] + [block] + lines[insert_at:]
    path.write_text("".join(new_lines), encoding="utf-8")
    return True


def main() -> None:
    changed: list[str] = []
    for rel, (name, doc) in TARGETS.items():
        p = Path(rel)
        if not p.exists():
            raise SystemExit(f"Missing expected file: {rel}")
        if _ensure_markers(p, name, doc):
            changed.append(rel)

    if changed:
        print("OK: added contract markers to:")
        for c in changed:
            print(f" - {c}")
    else:
        print("OK: no changes (already compliant).")


if __name__ == "__main__":
    main()
