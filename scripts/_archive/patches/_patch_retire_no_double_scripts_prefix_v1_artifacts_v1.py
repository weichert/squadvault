from __future__ import annotations

from pathlib import Path
import re

GATE_V1 = Path("scripts/gate_no_double_scripts_prefix_v1.sh")
GATE_V2 = Path("scripts/gate_no_double_scripts_prefix_v2.sh")

LEGACY_WRAPPERS = [
    Path("scripts/patch_prove_ci_add_no_double_scripts_prefix_gate_v1.sh"),
    Path("scripts/patch_fix_no_double_scripts_prefix_false_positives_v1.sh"),
]

LEGACY_PATCHERS = [
    Path("scripts/_patch_prove_ci_add_no_double_scripts_prefix_gate_v1.py"),
    Path("scripts/_patch_prove_ci_upgrade_no_double_scripts_prefix_gate_v2.py"),
    Path("scripts/_patch_fix_no_double_scripts_prefix_false_positives_v1.py"),
]

INSERT_WRAPPER_V2 = Path("scripts/patch_prove_ci_insert_under_docs_gates_anchor_v2.sh")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text, encoding="utf-8")


def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")


def _must_exist(p: Path) -> None:
    if not p.exists():
        _refuse(f"missing required file: {p}")


def _patch_gate_v1_to_shim() -> None:
    _must_exist(GATE_V1)
    _must_exist(GATE_V2)

    shim = """#!/usr/bin/env bash
set -euo pipefail

echo "=== Gate: no double scripts prefix (v1) — RETIRED (shim to v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Delegate to canonical v2 gate.
bash scripts/gate_no_double_scripts_prefix_v2.sh
"""
    _write(GATE_V1, shim)


def _patch_legacy_wrapper_to_retired_notice(p: Path) -> None:
    _must_exist(p)
    s = _read(p)

    retired = f"""#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: {p.name} — RETIRED ==="
echo "This legacy wrapper is retained for history, but the canonical guardrail is:"
echo "  scripts/gate_no_double_scripts_prefix_v2.sh"
echo "No action required."
exit 0
"""
    # Only overwrite if it still references the v1 gate path string (we’re cleaning greps)
    if ("gate_no_double_scripts_prefix_" in s) or ("no_double_scripts_prefix" in s):
        _write(p, retired)


def _patch_legacy_patcher_to_retired_notice(p: Path) -> None:
    _must_exist(p)
    s = _read(p)

    # Only rewrite if it hard-references the v1 gate filename/path (or tries to patch it).
    if "gate_no_double_scripts_prefix_v1" not in s and "gate_no_double_scripts_prefix_v2" not in s:
        return

    retired = f"""from __future__ import annotations

raise SystemExit(
    "RETired: {p.name}.\\n"
    "The canonical guardrail is scripts/gate_no_double_scripts_prefix_v2.sh.\\n"
    "No patch action required."
)
"""
    _write(p, retired)


def _patch_insert_wrapper_v2_keep_behavior_avoid_v1_ref() -> None:
    # Keep the v2 insertion wrapper as-is (it’s canonical), but ensure it doesn’t
    # accidentally reintroduce v1-gate references (it shouldn’t).
    _must_exist(INSERT_WRAPPER_V2)
    s = _read(INSERT_WRAPPER_V2)
    # No-op: leave contents unchanged unless we detect a literal v1 reference.
    if "gate_no_double_scripts_prefix_v1" in s:
        s = s.replace("gate_no_double_scripts_prefix_v1", "gate_no_double_scripts_prefix_v2")
        _write(INSERT_WRAPPER_V2, s)


def main() -> None:
    _patch_gate_v1_to_shim()

    for w in LEGACY_WRAPPERS:
        _patch_legacy_wrapper_to_retired_notice(w)

    for p in LEGACY_PATCHERS:
        _patch_legacy_patcher_to_retired_notice(p)

    _patch_insert_wrapper_v2_keep_behavior_avoid_v1_ref()


if __name__ == "__main__":
    main()
