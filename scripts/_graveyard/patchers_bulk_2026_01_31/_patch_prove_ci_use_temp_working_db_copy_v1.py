#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

MARK = "SV_PATCH: use temp working DB copy for fixture DB (explicit, v1)"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    if MARK in s:
        print("OK: prove_ci already patched for working DB copy.")
        return

    lines = s.splitlines()

    # Insert after fixture_files array is built + recorded.
    # We'll insert right after the "record" line.
    insert_idx = None
    for i, ln in enumerate(lines):
        if "check_fixture_immutability_ci.sh record" in ln:
            insert_idx = i + 1
            break
    if insert_idx is None:
        raise SystemExit("ERROR: could not find fixture immutability record line in prove_ci.sh")

    block = [
        f"# {MARK}",
        "# --- Fixture DB working copy (explicit) ---",
        "# Proofs may write to the DB; committed fixtures must remain immutable.",
        'FIXTURE_DB="fixtures/ci_squadvault.sqlite"',
        'WORK_DB="${FIXTURE_DB}"',
        'if [[ -f "${FIXTURE_DB}" ]]; then',
        '  echo "==> CI safety: using temp working DB copy (fixture remains immutable)"',
        '  WORK_DB="$(mktemp "${TMPDIR:-/tmp}/squadvault_ci_workdb.XXXXXX.sqlite")"',
        '  cleanup_work_db() { rm -f "${WORK_DB}" >/dev/null 2>&1 || true; }',
        '  trap cleanup_work_db EXIT',
        '  cp -p "${FIXTURE_DB}" "${WORK_DB}"',
        '  echo "    fixture_db=${FIXTURE_DB}"',
        '  echo "    working_db=${WORK_DB}"',
        'fi',
        "# --- /Fixture DB working copy ---",
        "",
    ]

    new_lines = []
    new_lines.extend(lines[:insert_idx])
    new_lines.extend(block)
    new_lines.extend(lines[insert_idx:])

    out = "\n".join(new_lines) + "\n"

    # Replace hardcoded fixture DB uses in prove_ci.sh with WORK_DB
    out = out.replace("--db fixtures/ci_squadvault.sqlite", '--db "${WORK_DB}"')

    TARGET.write_text(out, encoding="utf-8")
    print("OK: patched prove_ci.sh to run DB-writing proofs against WORK_DB temp copy.")

if __name__ == "__main__":
    main()
