from __future__ import annotations

from pathlib import Path
import runpy
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

PATCHERS = [
    "scripts/_patch_gate_ci_registry_execution_alignment_exclude_prove_ci_v1.py",
    "scripts/_patch_registry_add_ci_execution_exempt_locals_v1.py",
]


def main() -> None:
    for rel in PATCHERS:
        p = REPO_ROOT / rel
        if not p.exists():
            raise SystemExit(f"ERROR: missing patcher: {rel}")
        # Execute patcher as if it were run as __main__ (deterministic, no import side effects)
        runpy.run_path(str(p), run_name="__main__")


if __name__ == "__main__":
    sys.exit(main() or 0)
