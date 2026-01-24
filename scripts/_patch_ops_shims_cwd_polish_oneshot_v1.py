#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PATCHERS = [
    "scripts/_patch_prove_golden_path_add_script_dir_repo_root_v1.py",
    "scripts/_patch_check_shims_compliance_add_script_dir_repo_root_v1.py",
    "scripts/_patch_check_shims_compliance_use_repo_root_paths_v2.py",
    "scripts/_patch_ops_shims_cwd_independence_v1.py",
    "scripts/_patch_recap_sh_single_exec_bash_v1.py",
    "scripts/_patch_check_golden_path_recap_default_recap_script_py_v1.py",
]

def run(patcher: str) -> None:
    path = REPO_ROOT / patcher
    if not path.exists():
        raise SystemExit(f"ERROR: missing patcher: {patcher}")
    cmd = [str(REPO_ROOT / "scripts/py"), str(path)]
    r = subprocess.run(cmd, text=True)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

def main() -> int:
    for patcher in PATCHERS:
        run(patcher)
    print("OK: ops shim + CWD-independence polish one-shot applied (idempotent).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
