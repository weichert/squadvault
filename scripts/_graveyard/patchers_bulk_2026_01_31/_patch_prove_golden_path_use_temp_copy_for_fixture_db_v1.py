#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_golden_path.sh")
MARK = "SV_PATCH: if db is fixtures/*, run against temp copy (fixture immutable)"

SNIPPET = r'''
# --- Fixture DB write-safety (explicit) ---
# If the DB path points at a committed fixture, we MUST NOT write into it.
# Run the proof against a throwaway temp copy, preserving fixture immutability.
if [[ "${db}" == fixtures/* && -f "${db}" ]]; then
  echo "==> CI safety: DB is a fixture; using temp working copy (fixture remains immutable)"
  tmp_db="$(mktemp "${TMPDIR:-/tmp}/squadvault_fixture_db.XXXXXX.sqlite")"
  cleanup_tmp_db() { rm -f "${tmp_db}" >/dev/null 2>&1 || true; }
  trap cleanup_tmp_db EXIT

  cp -p "${db}" "${tmp_db}"
  echo "    fixture_db=${db}"
  echo "    working_db=${tmp_db}"
  db="${tmp_db}"
fi
# --- /Fixture DB write-safety (explicit) ---
'''.strip("\n")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    if MARK in s:
        print("OK: Golden path prove patch already applied.")
        return

    lines = s.splitlines()

    insert_idx = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith("db="):
            insert_idx = i + 1
            break

    if insert_idx is None:
        for i, ln in enumerate(lines):
            if "cd" in ln and "REPO_ROOT" in ln:
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
    print("OK: patched prove_golden_path.sh to use temp db when db is fixtures/*.")

if __name__ == "__main__":
    main()
