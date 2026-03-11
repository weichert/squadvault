from __future__ import annotations

from pathlib import Path

REGISTRY = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")
GUARDRAILS = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

# Current lines (as observed)
OLD_NAC_BULLET = (
    "- **NAC fingerprint preflight normalization (Golden Path):** "
    "`scripts/prove_golden_path.sh` normalizes placeholder "
    "`Selection fingerprint: test-fingerprint` to a **64-lower-hex** fingerprint "
    "before running the NAC harness (required by `Tests/_nac_check_assembly_plain_v1.py`)."
)

# Replace with a bullet that is correct post-v3 AND includes ephemeral exports behavior.
NEW_NAC_BULLET = (
    "- **NAC fingerprint preflight normalization (Golden Path):** "
    "`scripts/prove_golden_path.sh` detects placeholder "
    "`Selection fingerprint: test-fingerprint` and normalizes it to a **64-lower-hex** fingerprint "
    "**in a temp copy used only for NAC validation (non-mutating)** before running the NAC harness "
    "(required by `Tests/_nac_check_assembly_plain_v1.py`). "
    "**Exports are ephemeral by default** (temp export root); set `SV_KEEP_EXPORTS=1` to persist exports under `artifacts/`."
)

# Also enrich the scripts/prove_golden_path.sh entry in the proof surface registry list.
OLD_GP_LINE = "- scripts/prove_golden_path.sh — Proves canonical operator golden path via shims and gates."
NEW_GP_LINE = (
    "- scripts/prove_golden_path.sh — Proves canonical operator golden path via shims and gates "
    "(exports ephemeral by default; set `SV_KEEP_EXPORTS=1` to persist; NAC normalization is non-mutating)."
)

def patch_one(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"ERROR: missing file: {path}")

    text = path.read_text(encoding="utf-8")

    if OLD_NAC_BULLET in text:
        text = text.replace(OLD_NAC_BULLET, NEW_NAC_BULLET, 1)
    elif NEW_NAC_BULLET in text:
        pass
    else:
        # If the NAC bullet already changed (e.g., by an earlier patcher), we still want to append the exports note
        # without guessing. Fail fast so the patch remains deterministic.
        raise SystemExit(f"ERROR: NAC bullet anchor not found (or already diverged) in {path}")

    if path.name == REGISTRY.name:
        if OLD_GP_LINE in text and NEW_GP_LINE not in text:
            text = text.replace(OLD_GP_LINE, NEW_GP_LINE, 1)

    path.write_text(text, encoding="utf-8")
    print(f"Patched: {path}")

def main() -> int:
    patch_one(REGISTRY)
    patch_one(GUARDRAILS)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
