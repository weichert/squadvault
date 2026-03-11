from __future__ import annotations

from pathlib import Path


TARGET = Path("scripts/prove_ci.sh")

EXPORT_BLOCK = """\
# CI: ensure downstream scripts read the finalized working DB (after mktemp + copy)
export CI_WORK_DB="${WORK_DB}"
export WORK_DB="${WORK_DB}"
"""


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target file: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    if 'export CI_WORK_DB="${WORK_DB}"' in s and 'export WORK_DB="${WORK_DB}"' in s:
        print("OK: exports already present; no change.")
        return

    lines = s.splitlines(True)

    # Strategy A (preferred): insert immediately after the line that copies into WORK_DB.
    insert_idx = None
    for i, line in enumerate(lines):
        l = line.strip()
        if l.startswith("#"):
            continue
        # Match: cp ... "$WORK_DB"
        if l.startswith("cp ") and '"$WORK_DB"' in l:
            insert_idx = i + 1
            break

    # Strategy B (fallback): insert after the last WORK_DB assignment.
    if insert_idx is None:
        last_assign = None
        for i, line in enumerate(lines):
            l = line.strip()
            if l.startswith("#"):
                continue
            if l.startswith("WORK_DB="):
                last_assign = i + 1

        if last_assign is None:
            raise SystemExit(
                "ERROR: could not find a safe anchor (no cp ... \"$WORK_DB\" line, and no WORK_DB= assignment). "
                "Refusing to patch."
            )
        insert_idx = last_assign

    block = "\n" + EXPORT_BLOCK
    if not block.endswith("\n"):
        block += "\n"

    new_lines = lines[:insert_idx] + [block] + lines[insert_idx:]
    new_s = "".join(new_lines)

    if new_s == s:
        raise SystemExit("ERROR: patch produced no changes (unexpected).")

    TARGET.write_text(new_s, encoding="utf-8")
    print(f"OK: patched {TARGET} (inserted exports after final WORK_DB anchor).")


if __name__ == "__main__":
    main()
