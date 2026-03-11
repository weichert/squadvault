from __future__ import annotations

from pathlib import Path

REG_PATH = Path("docs/80_indices/ops/Creative_Surface_Registry_v1.0.md")

REG_TEXT = """# Creative Surface Registry (v1.0)

Status: CANONICAL (registry)

This registry lists canonical Creative Surface runners, gates, and proofs.
It exists to make creative generation **discoverable** and CI-enforceable.

## How to run (local)

This phase is wired later into CI; for now, planned entrypoints:

- Generator: `scripts/gen_creative_sharepack_v1.py`
- Gate: `scripts/gate_creative_sharepack_output_contract_v1.sh`
- Proof: `scripts/prove_creative_sharepack_determinism_v1.sh`

## Registry Entries

<!-- SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_BEGIN -->
- `scripts/gen_creative_sharepack_v1.py` — Generate creative sharepack bundle (v1)
- `scripts/gate_creative_sharepack_output_contract_v1.sh` — Gate: creative sharepack output contract (v1)
- `scripts/prove_creative_sharepack_determinism_v1.sh` — Proof: creative sharepack determinism (v1)
<!-- SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_END -->
"""

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")

def main() -> None:
    if REG_PATH.exists():
        cur = _read(REG_PATH)
        if cur == REG_TEXT:
            print("OK")
            return
        raise SystemExit(
            f"REFUSE: {REG_PATH} exists but does not match expected v1.0 content. "
            "Manual edits detected; update patcher intentionally."
        )

    _write(REG_PATH, REG_TEXT)
    print("OK")

if __name__ == "__main__":
    main()
