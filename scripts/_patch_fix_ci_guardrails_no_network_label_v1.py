#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

OLD = "scripts/gate_no_network_in_ci_proofs_v1.sh\tNo network in CI proofs gate (v1)\n"
NEW = "scripts/gate_no_network_in_ci_proofs_v1.sh\tNo network/package-manager actions in CI proofs (v1)\n"

def main() -> int:
    if not REGISTRY.is_file():
        raise RuntimeError(f"missing registry: {REGISTRY}")

    text = REGISTRY.read_text(encoding="utf-8")
    if NEW in text:
        return 0
    if OLD not in text:
        raise RuntimeError("expected old no-network registry row not found")
    REGISTRY.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
