#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
PROVE = REPO / "scripts" / "prove_ci.sh"
INDEX = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
REGISTRY = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"

GATE_LINE = "bash scripts/gate_ci_guardrails_surface_freeze_v1.sh\n"
REGISTRY_LINE = (
    "scripts/gate_ci_guardrails_surface_freeze_v1.sh\t"
    "CI guardrails surface freeze gate (v1)\n"
)
INDEX_BULLET = (
    "- scripts/gate_ci_guardrails_surface_freeze_v1.sh — "
    "CI guardrails surface freeze gate (v1)\n"
)

PROVE_ANCHOR = "bash scripts/gate_ci_guardrails_registry_completeness_v1.sh\n"
INDEX_ANCHOR = (
    "- scripts/gate_ci_guardrails_registry_completeness_v1.sh — "
    "CI guardrails registry completeness gate (v1)\n"
)
REGISTRY_ANCHOR = (
    "scripts/gate_ci_guardrails_registry_completeness_v1.sh\t"
    "CI guardrails registry completeness gate (v1)\n"
)


def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)


def patch_prove() -> None:
    text = PROVE.read_text(encoding="utf-8")
    if GATE_LINE in text:
        print("OK: prove_ci.sh already contains CI guardrails surface freeze gate")
        return
    if PROVE_ANCHOR not in text:
        die("ERROR: could not find registry completeness anchor in scripts/prove_ci.sh")
    text = text.replace(PROVE_ANCHOR, PROVE_ANCHOR + GATE_LINE, 1)
    PROVE.write_text(text, encoding="utf-8")
    print("OK: wired CI guardrails surface freeze gate into scripts/prove_ci.sh")


def patch_registry() -> None:
    text = REGISTRY.read_text(encoding="utf-8")
    if REGISTRY_LINE in text:
        print("OK: registry already contains CI guardrails surface freeze gate")
        return
    if REGISTRY_ANCHOR not in text:
        die("ERROR: could not find registry completeness anchor in CI_Guardrail_Entrypoint_Labels_v1.tsv")
    text = text.replace(REGISTRY_ANCHOR, REGISTRY_ANCHOR + REGISTRY_LINE, 1)
    REGISTRY.write_text(text, encoding="utf-8")
    print("OK: updated CI_Guardrail_Entrypoint_Labels_v1.tsv")


def patch_index() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if INDEX_BULLET in text:
        print("OK: index already contains CI guardrails surface freeze gate")
        return
    if INDEX_ANCHOR not in text:
        die("ERROR: could not find registry completeness bullet in CI_Guardrails_Index_v1.0.md")
    text = text.replace(INDEX_ANCHOR, INDEX_ANCHOR + INDEX_BULLET, 1)
    INDEX.write_text(text, encoding="utf-8")
    print("OK: updated CI_Guardrails_Index_v1.0.md")


def main() -> int:
    if not PROVE.is_file():
        die("ERROR: missing scripts/prove_ci.sh")
    if not INDEX.is_file():
        die("ERROR: missing docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
    if not REGISTRY.is_file():
        die("ERROR: missing docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv")

    patch_prove()
    patch_registry()
    patch_index()
    return 0


if __name__ == "__main__":
    sys.exit(main())
