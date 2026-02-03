from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

OLD_EXPORT_1 = 'export CI_WORK_DB="${WORK_DB}"  # prove_ci_export_ci_work_db_v2'
OLD_EXPORT_2 = 'export WORK_DB="${WORK_DB}"     # prove_ci_export_ci_work_db_v2'

CP_ANCHOR = 'cp -p "${FIXTURE_DB}" "${WORK_DB}"'

NEW_BLOCK = """\
# CI: ensure downstream scripts read the finalized working DB (after mktemp + copy)
export CI_WORK_DB="${WORK_DB}"
export WORK_DB="${WORK_DB}"
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target file: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    # 1) Remove the old (early) exports (must remove exactly those v2-tagged lines)
    removed = 0
    new_lines: list[str] = []
    for line in lines:
        if line.rstrip("\n") == OLD_EXPORT_1:
            removed += 1
            continue
        if line.rstrip("\n") == OLD_EXPORT_2:
            removed += 1
            continue
        new_lines.append(line)

    if removed == 0:
        raise SystemExit(
            "ERROR: did not find the expected v2 export lines to remove. "
            "Refusing to patch to avoid duplicating exports."
        )

    # 2) Insert the new export block immediately after the cp anchor
    insert_idx = None
    for i, line in enumerate(new_lines):
        if line.strip() == CP_ANCHOR:
            insert_idx = i + 1
            break

    if insert_idx is None:
        raise SystemExit(
            f'ERROR: could not find cp anchor line: {CP_ANCHOR!r}. Refusing to patch.'
        )

    # guard: don't double-insert if block already present right after cp
    window = "".join(new_lines[insert_idx:insert_idx+6])
    if 'export CI_WORK_DB="${WORK_DB}"' in window and 'export WORK_DB="${WORK_DB}"' in window:
        raise SystemExit("ERROR: exports already present after cp anchor; refusing to duplicate.")

    block = "\n" + NEW_BLOCK
    if not block.endswith("\n"):
        block += "\n"

    patched_lines = new_lines[:insert_idx] + [block] + new_lines[insert_idx:]
    out = "".join(patched_lines)

    if out == s:
        raise SystemExit("ERROR: patch produced no changes (unexpected).")

    TARGET.write_text(out, encoding="utf-8")
    print(f"OK: patched {TARGET} (removed early exports; inserted exports after cp into WORK_DB).")

if __name__ == "__main__":
    main()
