from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
).stdout.strip())

SCRIPTS = ROOT / "scripts"
GRAVEYARD_PREFIX = "scripts/_graveyard/"


def sh_wrapper_text(patcher_rel: str, wrapper_rel: str) -> str:
    patcher_base = Path(patcher_rel).name
    return f"""#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: {wrapper_rel} ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${{PYTHON:-python}}"
fi

"$PY" "{patcher_rel}"

echo "==> bash syntax check"
bash -n "{wrapper_rel}"

echo "OK"
"""


def main() -> int:
    # Only consider git-tracked patchers; match gate behavior.
    patchers = subprocess.run(
        ["git", "ls-files", "scripts/_patch_*.py"],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    ).stdout.splitlines()

    created = 0
    skipped = 0

    for p in patchers:
        if not p or p.startswith(GRAVEYARD_PREFIX):
            skipped += 1
            continue
        p_path = ROOT / p
        if not p_path.exists():
            continue

        base = Path(p).name             # _patch_foo.py
        if not base.startswith("_patch_") or not base.endswith(".py"):
            continue
        stem = base[:-3]                # _patch_foo
        wrapper = f"scripts/{stem[1:]}.sh"  # patch_foo.sh

        w_path = ROOT / wrapper
        if w_path.exists():
            continue

        w_path.write_text(sh_wrapper_text(p, wrapper), encoding="utf-8")
        w_path.chmod(0o755)
        created += 1
        print(f"CREATED: {wrapper}")

    print(f"OK: wrappers created: {created} (skipped graveyard/other: {skipped})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
