from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")

START_ANCHOR = r"# os\.walk\(\): do NOT flag if dirs\.sort\(\) and files\.sort\(\) appear within next 5 lines"
# We’ll patch the small block that assigns py_hits_oswalk_raw and then enters the loop.

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if "oswalk_parse_hardening_v1" in s:
        print("NO-OP: already patched (oswalk_parse_hardening_v1)")
        return

    if not re.search(START_ANCHOR, s):
        raise SystemExit("FAIL: could not find os.walk gate anchor")

    # Patch 1: after filter_exclusions, keep only lines that look like "path:123:"
    # Patch 2: inside loop, skip if ln is not numeric (defensive)
    s2 = s

    # 1) Tighten py_hits_oswalk_raw assignment
    s2, n1 = re.subn(
        r'(py_hits_oswalk_raw="\$\(\s*printf "%s\\n" "\$\{py_hits_oswalk_raw\}" \| filter_exclusions \|\| true\s*\)"\n)',
        r'\1'
        r'# oswalk_parse_hardening_v1: only accept grep -n shaped hits: "file:NNN:"\n'
        r'py_hits_oswalk_raw="$(printf "%s\n" "${py_hits_oswalk_raw}" | grep -E \'^[^:]+:[0-9]+:\' || true)"\n',
        s2,
        count=1,
    )
    if n1 != 1:
        # Fallback: match the line more loosely
        s2, n1b = re.subn(
            r'py_hits_oswalk_raw="\$\(\s*printf "%s\\n" "\$\{py_hits_oswalk_raw\}" \| filter_exclusions \|\| true\s*\)"\n',
            'py_hits_oswalk_raw="$(printf "%s\\n" "${py_hits_oswalk_raw}" | filter_exclusions || true)"\n'
            '# oswalk_parse_hardening_v1: only accept grep -n shaped hits: "file:NNN:"\n'
            'py_hits_oswalk_raw="$(printf "%s\\n" "${py_hits_oswalk_raw}" | grep -E \'^[^:]+:[0-9]+:\' || true)"\n',
            s2,
            count=1,
        )
        if n1b != 1:
            raise SystemExit("FAIL: could not patch py_hits_oswalk_raw filter block")

    # 2) Add numeric guard after ln= extraction
    guard_snippet = (
        '    ln="$(printf "%s" "${hit}" | cut -d: -f2)"\n'
        '    # oswalk_parse_hardening_v1: defensive; ignore non-numeric line fields\n'
        '    printf "%s" "${ln}" | grep -E -q \'^[0-9]+$\' || continue\n'
    )

    s2, n2 = re.subn(
        r'(\s+ln="\$\(\s*printf "%s" "\$\{hit\}" \| cut -d: -f2\s*\)"\n)',
        guard_snippet,
        s2,
        count=1,
    )
    if n2 != 1:
        raise SystemExit("FAIL: could not inject ln numeric guard in os.walk loop")

    TARGET.write_text(s2, encoding="utf-8", newline="\n")
    print("OK: patched os.walk hit parsing hardening (v1)")

if __name__ == "__main__":
    main()
