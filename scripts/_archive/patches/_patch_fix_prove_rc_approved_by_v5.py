#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

def main() -> int:
    s = TARGET.read_text()
    orig = s

    # 1) Remove approved_by from the required-args gate.
    # Match the exact pattern your grep showed.
    s = re.sub(
        r'(?m)^\s*if\s+\[\[\s+-z\s+"\$\{db\}"\s+\|\|\s+-z\s+"\$\{league_id\}"\s+\|\|\s+-z\s+"\$\{season\}"\s+\|\|\s+-z\s+"\$\{week_index\}"\s+\|\|\s+-z\s+"\$\{approved_by\}"\s*\]\];\s*then\s*$',
        'if [[ -z "${db}" || -z "${league_id}" || -z "${season}" || -z "${week_index}" ]]; then',
        s,
    )

    # 2) Update Usage synopsis to make --approved-by optional.
    s = re.sub(
        r'(?m)^(  \./scripts/prove_rivalry_chronicle_end_to_end_v1\.sh .*?--week-index N)\s+--approved-by NAME\s*$',
        r'\1 [--approved-by NAME]',
        s,
    )

    if s == orig:
        print("ERROR: could not find expected required-args gate / usage line to patch (script drift?)")
        return 2

    TARGET.write_text(s)
    print(f"OK: patched {TARGET} (approved_by optional; usage updated)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
