from __future__ import annotations

import sys
from pathlib import Path

CANONICAL = "out"

REG_PATH = Path("docs/80_indices/ops/Creative_Surface_Registry_v1.0.md")
OPS_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

REG_BEGIN = "<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_BEGIN -->"
REG_END = "<!-- SV_CREATIVE_SURFACE_REGISTRY_V1_END -->"

OPS_BEGIN = "<!-- SV_CREATIVE_SHAREPACK_GUARDRAILS_v1_BEGIN -->"
OPS_END = "<!-- SV_CREATIVE_SHAREPACK_GUARDRAILS_v1_END -->"

ENTRY_MARK = "SV_CREATIVE_SURFACE_REGISTRY_DOC_ENTRY_v1"


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, s: str) -> bool:
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    if old == s:
        return False
    p.write_text(s, encoding="utf-8", newline="\n")
    return True


def _render_registry_doc() -> str:
    return f"""# Creative Surface Registry v1.0

This document is a **machine-indexed registry surface** for the Creative Surface.

{REG_BEGIN}
## Canonical Surfaces

- **Fingerprint generator**: `scripts/gen_creative_surface_fingerprint_v1.py`
- **Canonical fingerprint artifact**: `artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json`
- **Canonical gate**: `scripts/gate_creative_surface_fingerprint_canonical_v1.sh`
- **Related contract**: `docs/contracts/creative_sharepack_output_contract_v1.md`

## Scope (authoritative)

The Creative Surface Fingerprint is computed from git-tracked paths, then restricted by an explicit scope allowlist/denylist in:

- `scripts/gen_creative_surface_fingerprint_v1.py` (`SV_CREATIVE_SURFACE_SCOPE_V1`)

{REG_END}
""".rstrip() + "\n"


def _patch_ops_index(s: str) -> str:
    if OPS_BEGIN not in s or OPS_END not in s:
        _die("Ops index missing expected bounded markers for Creative Sharepack guardrails; refusing to patch")

    if "Creative_Surface_Registry_v1.0.md" in s or ENTRY_MARK in s:
        return CANONICAL

    entry = (
        f"<!-- {ENTRY_MARK} -->\n"
        "- **Creative Surface Registry**  \n"
        "  `docs/80_indices/ops/Creative_Surface_Registry_v1.0.md`\n"
    )

    pre, rest = s.split(OPS_BEGIN, 1)
    mid, post = rest.split(OPS_END, 1)

    # Insert just before end marker (keeps it inside bounded block)
    out_mid = mid.rstrip() + "\n" + entry + "\n"
    out = pre + OPS_BEGIN + out_mid + OPS_END + post

    # minimal sanity
    if OPS_BEGIN not in out or OPS_END not in out:
        _die("patch corrupted bounded markers; refusing")

    return out


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    reg = repo_root / REG_PATH
    ops = repo_root / OPS_INDEX

    if not ops.exists():
        _die(f"missing ops index: {OPS_INDEX}")

    reg_doc = _render_registry_doc()
    reg_changed = _write_if_changed(reg, reg_doc)

    ops_s = _read(ops)
    patched_ops = _patch_ops_index(ops_s)
    if patched_ops == CANONICAL:
        ops_changed = False
    else:
        ops_changed = _write_if_changed(ops, patched_ops)

    if not reg_changed and not ops_changed:
        print("OK: creative surface registry doc + ops discoverability already canonical (noop)")
        return 0

    print("OK: patched creative surface registry doc + ops discoverability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
