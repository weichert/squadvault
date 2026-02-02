from __future__ import annotations

from pathlib import Path

DEPRECATION = """\
# DEPRECATED — DO NOT USE
# Superseded by:
#   scripts/_patch_prove_golden_path_pin_pytest_list_v3.py
#
# This patcher is retained for audit/history only.
# Golden Path pytest pinning was finalized in v3.
"""

# Best-effort list (skip missing files):
CANDIDATES = [
    "scripts/_patch_prove_golden_path_pin_pytest_list_v1.py",
    "scripts/_patch_prove_golden_path_pin_pytest_list_v2.py",
    "scripts/_patch_prove_golden_path_remove_pytest_dir_invocation_v1.py",
    "scripts/_patch_prove_golden_path_remove_pytest_dir_invocation_v2.py",
    # Gitignore allowlist helpers that were part of the iterative path:
    "scripts/_patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v1.py",
    "scripts/_patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v2.py",
    "scripts/_patch_gitignore_allow_prove_golden_path_remove_pytest_dir_invocation_patcher_v1.py",
    "scripts/_patch_gitignore_allow_prove_golden_path_remove_pytest_dir_invocation_patcher_v2.py",
]

def main() -> None:
    for p in CANDIDATES:
        path = Path(p)
        if not path.exists():
            continue

        s = path.read_text(encoding="utf-8")
        if s.startswith(DEPRECATION):
            continue

        # Insert at top; if file starts with shebang, keep it first.
        if s.startswith("#!"):
            first_line, rest = s.split("\n", 1)
            new = first_line + "\n" + DEPRECATION + "\n" + rest
        else:
            new = DEPRECATION + "\n" + s

        path.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    main()
