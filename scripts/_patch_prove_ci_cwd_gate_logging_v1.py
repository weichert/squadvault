from __future__ import annotations
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

OLD_BLOCK = """\
echo "=== Gate: CWD independence (shims) v1 ==="
repo_root_for_gate="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
bash "${repo_root_for_gate}/scripts/gate_cwd_independence_shims_v1.sh"
"""

NEW_BLOCK = """\
echo "=== Gate: CWD independence (shims) v1 ==="
repo_root_for_gate="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
gate_path="${repo_root_for_gate}/scripts/gate_cwd_independence_shims_v1.sh"
echo "    repo_root_for_gate=${repo_root_for_gate}"
echo "    gate_path=${gate_path}"
if [[ ! -f "${gate_path}" ]]; then
  echo "ERROR: missing CWD gate: ${gate_path}"
  exit 1
fi
bash "${gate_path}"
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if OLD_BLOCK not in s:
        raise SystemExit(
            "ERROR: could not find the expected CWD gate block to replace.\n"
            "Refusing to guess. (Has prove_ci.sh drifted?)"
        )

    s2 = s.replace(OLD_BLOCK, NEW_BLOCK, 1)
    TARGET.write_text(s2, encoding="utf-8")
    print("OK: upgraded CWD gate block with logging + existence check (v1).")

if __name__ == "__main__":
    main()
