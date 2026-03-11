from __future__ import annotations

from pathlib import Path

FILES = [
    Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
]

OLD_NAC_BULLET = (
    "- **NAC fingerprint preflight normalization (Golden Path):** "
    "`scripts/prove_golden_path.sh` normalizes placeholder "
    "`Selection fingerprint: test-fingerprint` to a **64-lower-hex** fingerprint "
    "before running the NAC harness (required by `Tests/_nac_check_assembly_plain_v1.py`)."
)

NEW_NAC_BULLET = (
    "- **NAC fingerprint preflight normalization (Golden Path):** "
    "`scripts/prove_golden_path.sh` detects placeholder "
    "`Selection fingerprint: test-fingerprint` and normalizes it to a **64-lower-hex** fingerprint "
    "**in a temp copy used only for NAC validation (non-mutating)** before running the NAC harness "
    "(required by `Tests/_nac_check_assembly_plain_v1.py`)."
)

NEW_DB_BULLET = (
    "- **Golden Path default DB (fresh clone safety):** "
    "If no DB env is provided and the default `.local_squadvault.sqlite` is missing or lacks required schema, "
    "`scripts/prove_golden_path.sh` uses a **fixture-derived temp DB copy** (`fixtures/ci_squadvault.sqlite` → mktemp) "
    "and exports `SQUADVAULT_TEST_DB` for pytest."
)

def patch_file(p: Path) -> None:
    if not p.exists():
        raise SystemExit(f"ERROR: missing file: {p}")

    text = p.read_text(encoding="utf-8")

    if OLD_NAC_BULLET not in text and NEW_NAC_BULLET not in text:
        raise SystemExit(f"ERROR: expected NAC bullet not found in {p}")

    # Replace NAC bullet (idempotent)
    if OLD_NAC_BULLET in text:
        text = text.replace(OLD_NAC_BULLET, NEW_NAC_BULLET, 1)

    # Ensure DB bullet present immediately after NAC bullet (idempotent)
    if NEW_DB_BULLET not in text:
        anchor = NEW_NAC_BULLET
        if anchor not in text:
            raise SystemExit(f"ERROR: cannot anchor DB bullet insertion in {p}")
        text = text.replace(anchor, anchor + "\n" + NEW_DB_BULLET, 1)

    # In CI_Proof_Surface_Registry, also enrich the prove_golden_path entry if present (idempotent)
    if p.name == "CI_Proof_Surface_Registry_v1.0.md":
        old_gp_line = "- scripts/prove_golden_path.sh — Proves canonical operator golden path via shims and gates."
        new_gp_line = (
            "- scripts/prove_golden_path.sh — Proves canonical operator golden path via shims and gates "
            "(fresh-clone safe: fixture-derived temp DB when default DB missing/invalid schema; NAC normalization is non-mutating)."
        )
        if old_gp_line in text and new_gp_line not in text:
            text = text.replace(old_gp_line, new_gp_line, 1)

    p.write_text(text, encoding="utf-8")
    print(f"Patched: {p}")

def main() -> int:
    for p in FILES:
        patch_file(p)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
