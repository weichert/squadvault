from __future__ import annotations

import sys
from pathlib import Path

CANONICAL = "out"

PROVE = Path("scripts/prove_ci.sh")
OPS = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

OPS_BEGIN = "<!-- SV_CREATIVE_SHAREPACK_GUARDRAILS_v1_BEGIN -->"
OPS_END = "<!-- SV_CREATIVE_SHAREPACK_GUARDRAILS_v1_END -->"

ENTRY_MARK = "SV_CI_GUARDRAIL_GATE_CREATIVE_SURFACE_REGISTRY_PARITY_v1"

GATE_LINE = "bash scripts/gate_creative_surface_registry_parity_v1.sh"
GATE_BULLET = "- scripts/gate_creative_surface_registry_parity_v1.sh — Creative Surface Registry parity gate (v1)\n"


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_if_changed(p: Path, s: str) -> bool:
    old = p.read_text(encoding="utf-8")
    if old == s:
        return False
    p.write_text(s, encoding="utf-8", newline="\n")
    return True


def _patch_prove_ci(s: str) -> str:
    if GATE_LINE in s:
        return CANONICAL

    needle = "bash scripts/gate_creative_surface_fingerprint_canonical_v1.sh"
    idx = s.find(needle)
    if idx == -1:
        _die("could not find creative surface fingerprint canonical gate invocation in prove_ci to anchor insertion")

    insert_at = idx + len(needle)
    out = s[:insert_at] + "\n" + GATE_LINE + s[insert_at:]
    return out


def _patch_ops_index(s: str) -> str:
    if OPS_BEGIN not in s or OPS_END not in s:
        _die("ops index missing SV_CREATIVE_SHAREPACK_GUARDRAILS_v1 bounded markers")

    if "gate_creative_surface_registry_parity_v1.sh" in s or ENTRY_MARK in s:
        return CANONICAL

    entry = f"<!-- {ENTRY_MARK} -->\n" + GATE_BULLET

    pre, rest = s.split(OPS_BEGIN, 1)
    mid, post = rest.split(OPS_END, 1)

    out_mid = mid.rstrip() + "\n" + entry + "\n"
    return pre + OPS_BEGIN + out_mid + OPS_END + post


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    prove = repo_root / PROVE
    ops = repo_root / OPS

    if not prove.exists():
        _die("missing scripts/prove_ci.sh")
    if not ops.exists():
        _die("missing ops index")

    changed = False

    p = _read(prove)
    p2 = _patch_prove_ci(p)
    if p2 != CANONICAL:
        changed |= _write_if_changed(prove, p2)

    o = _read(ops)
    o2 = _patch_ops_index(o)
    if o2 != CANONICAL:
        changed |= _write_if_changed(ops, o2)

    if not changed:
        print("OK: registry parity gate wiring + discoverability already canonical (noop)")
        return 0

    print("OK: wired registry parity gate into prove_ci + indexed discoverability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
