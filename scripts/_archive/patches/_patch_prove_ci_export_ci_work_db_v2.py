from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")
MARK = "prove_ci_export_ci_work_db_v2"

def die(msg: str) -> None:
    raise SystemExit(msg)

def main() -> None:
    if not TARGET.exists():
        die(f"FAIL: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")

    if MARK in s:
        print("NO-OP: already patched (marker present)")
        return

    # Match:
    #   working_db=...
    #   local working_db=...
    #   WORK_DB=...
    #   local WORK_DB=...
    m = re.search(
        r"(?m)^(?P<indent>[ \t]*)(?:(?:local)[ \t]+)?(?P<var>working_db|WORK_DB)=(?P<rhs>.*)$",
        s,
    )
    if not m:
        die(
            "FAIL: could not find an assignment to working_db=... or WORK_DB=... "
            "in scripts/prove_ci.sh (unexpected format)"
        )

    var = m.group("var")
    indent = m.group("indent")
    insert_pos = m.end()

    export_block = (
        "\n"
        f'{indent}export CI_WORK_DB="${{{var}}}"  # {MARK}\n'
        f'{indent}export WORK_DB="${{{var}}}"     # {MARK}\n'
    )

    out = s[:insert_pos] + export_block + s[insert_pos:]
    TARGET.write_text(out, encoding="utf-8", newline="\n")
    print(f"OK: prove_ci now exports CI_WORK_DB/WORK_DB from {var} (v2)")

if __name__ == "__main__":
    main()
