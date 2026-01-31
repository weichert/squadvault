#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")
MARK = "SV_PATCH: rewrite --db fixtures/* to temp copy (arg-based, set -u safe)"

SNIPPET = r'''
# --- Fixture DB write-safety (explicit; arg-based; set -u safe) ---
# If caller passes --db fixtures/<...>, we must not write into the committed fixture.
# Instead run against a throwaway temp copy, preserving fixture immutability.
tmp_db=""
rewrite_db_arg_if_fixture() {
  local argv=()
  local i=0
  while [[ $i -lt $# ]]; do
    local a="${1}"; shift
    if [[ "${a}" == "--db" ]]; then
      if [[ $# -lt 1 ]]; then
        echo "ERROR: --db missing value" >&2
        exit 2
      fi
      local db_path="${1}"; shift
      if [[ "${db_path}" == fixtures/* && -f "${db_path}" ]]; then
        echo "==> CI safety: DB is a fixture; using temp working copy (fixture remains immutable)"
        tmp_db="$(mktemp "${TMPDIR:-/tmp}/squadvault_fixture_db.XXXXXX.sqlite")"
        cp -p "${db_path}" "${tmp_db}"
        echo "    fixture_db=${db_path}"
        echo "    working_db=${tmp_db}"
        argv+=("--db" "${tmp_db}")
      else
        argv+=("--db" "${db_path}")
      fi
    else
      argv+=("${a}")
    fi
    i=$((i+1))
  done

  # Replace positional args for the remainder of the script
  set -- "${argv[@]}"
}

cleanup_tmp_db() { [[ -n "${tmp_db}" ]] && rm -f "${tmp_db}" >/dev/null 2>&1 || true; }
trap cleanup_tmp_db EXIT

rewrite_db_arg_if_fixture "$@"
# --- /Fixture DB write-safety ---
'''.strip("\n")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    if MARK in s:
        print("OK: prove_golden_path already patched (arg-based).")
        return

    lines = s.splitlines()

    # Insert after strict mode line (set -euo pipefail) if present, else after shebang.
    insert_idx = None
    for i, ln in enumerate(lines):
        if "set -euo pipefail" in ln:
            insert_idx = i + 1
            break
    if insert_idx is None:
        insert_idx = 1 if (lines and lines[0].startswith("#!")) else 0

    new_lines = []
    new_lines.extend(lines[:insert_idx])
    new_lines.append(f"# {MARK}")
    new_lines.append(SNIPPET)
    new_lines.extend(lines[insert_idx:])

    TARGET.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("OK: patched prove_golden_path.sh to rewrite --db fixtures/* to temp copy (set -u safe).")

if __name__ == "__main__":
    main()
