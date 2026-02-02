from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v1.sh")

GOOD = """\
#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore allowlist Golden Path pytest pin patcher (v1) ==="
python="${PYTHON:-python}"

"$python" scripts/_patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v1.py

echo "==> verify allowlist present"
grep -n '^\\!scripts/_patch_prove_golden_path_pin_pytest_list_v1\\.py$' .gitignore >/dev/null
echo "OK"
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    cur = TARGET.read_text(encoding="utf-8")

    # If already normalized, idempotent no-op.
    if cur == GOOD:
        return

    # Refuse if this doesn't look like the intended wrapper (guard against patching wrong file).
    if "_patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v1.py" not in cur:
        raise SystemExit("ERROR: wrapper does not reference expected patcher; refusing")

    TARGET.write_text(GOOD, encoding="utf-8")

if __name__ == "__main__":
    main()
