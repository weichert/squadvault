from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if "oswalk_numeric_guard_v1" in s:
        print("NO-OP: already patched (oswalk_numeric_guard_v1)")
        return

    # Find the ln= assignment in the os.walk hit loop and inject a numeric guard immediately after.
    # We match the exact line you showed earlier:
    #   ln="$(printf "%s" "${hit}" | cut -d: -f2)"
    pat = re.compile(
        r'^(?P<indent>[ \t]*)ln="\$\(\s*printf "%s" "\$\{hit\}" \| cut -d: -f2\s*\)"\s*$',
        re.M,
    )
    m = pat.search(s)
    if not m:
        raise SystemExit("FAIL: could not find ln= assignment in os.walk loop")

    indent = m.group("indent")
    guard = (
        f"{indent}# oswalk_numeric_guard_v1: defensive; ignore non-numeric line fields\n"
        f"{indent}printf \"%s\" \"${{ln}}\" | grep -E -q '^[0-9]+$' || continue\n"
    )

    insert_at = m.end()
    s2 = s[:insert_at] + "\n" + guard + s[insert_at:]

    TARGET.write_text(s2, encoding="utf-8", newline="\n")
    print("OK: injected os.walk numeric ln guard (v1)")

if __name__ == "__main__":
    main()
