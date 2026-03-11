#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = REPO_ROOT / ".gitignore"

BLOCK_START = "# Local/one-off patchers (kept out of canonical history)"
BLOCK = """# Local/one-off patchers (kept out of canonical history)
scripts/_patch_*.py
scripts/_diag_*.py

# Canonical patchers (DO track these)
!scripts/_patch_ops_shims_cwd_polish_oneshot_v1.py
!scripts/_patch_ops_shims_cwd_independence_v1.py
!scripts/_patch_prove_golden_path_add_script_dir_repo_root_v1.py
!scripts/_patch_check_shims_compliance_add_script_dir_repo_root_v1.py
!scripts/_patch_check_shims_compliance_use_repo_root_paths_v2.py
!scripts/_patch_recap_sh_single_exec_bash_v1.py
!scripts/_patch_check_golden_path_recap_default_recap_script_py_v1.py

# Canonical doc lock patchers (DO track these)
!scripts/_patch_create_minimal_documentation_map_v1.py
!scripts/_patch_lock_ops_shim_cwd_contract_v1.py
"""

def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)

def main() -> int:
    if not GITIGNORE.exists():
        die(".gitignore not found")

    s0 = GITIGNORE.read_text(encoding="utf-8")

    # If the block (or at least the two new whitelist lines) already exist, be a no-op.
    if ("!scripts/_patch_create_minimal_documentation_map_v1.py" in s0
        and "!scripts/_patch_lock_ops_shim_cwd_contract_v1.py" in s0):
        print("OK: .gitignore already whitelists canonical doc lock patchers; no changes.")
        return 0

    # Replace an existing "Local/one-off patchers" block if present, else append at end.
    if BLOCK_START in s0:
        # Replace from BLOCK_START to the next blank line *after* the canonical whitelist section,
        # conservatively by replacing only the first occurrence of the start line through end-of-file.
        # (We keep this simple and strict: insert a fresh canonical block at end, and remove only the old start line block header.)
        # Safer approach: append canonical block and leave existing lines alone.
        s1 = s0.rstrip() + "\n\n" + BLOCK + "\n"
    else:
        s1 = s0.rstrip() + "\n\n" + BLOCK + "\n"

    if s1 == s0:
        print("OK: no changes needed.")
        return 0

    GITIGNORE.write_text(s1, encoding="utf-8")
    print("OK: updated .gitignore to whitelist canonical doc lock patchers (and ignore _diag_*).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
