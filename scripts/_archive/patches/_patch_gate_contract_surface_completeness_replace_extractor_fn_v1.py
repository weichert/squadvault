from __future__ import annotations

import re
from pathlib import Path

GATE = Path("scripts/gate_contract_surface_completeness_v1.sh")

BEGIN = "# SV_PATCH: extract_enforced_by_list_fn_v1_BEGIN"
END = "# SV_PATCH: extract_enforced_by_list_fn_v1_END"

FN = f"""\
extract_enforced_by_list() {{
  local doc="$1"

  local start
  start="$(grep -n '^##[[:space:]]\\+Enforced By[[:space:]]*$' "$doc" | head -n 1 | cut -d: -f1 || true)"
  if [[ -z "$start" ]]; then
    die "Missing required section '## Enforced By' in contract doc: $doc"
  fi

  local after="$((start + 1))"

  {BEGIN}
  # Extract bullet entries from the Enforced By section until the next "## " header.
  # Accept either:
  #   - `scripts/.../foo.sh`
  #   - scripts/.../foo.sh
  # Emit only the captured scripts/... path (no full-line replacement), and drop blanks.
  awk -v start="$after" 'NR>=start {{
    if ($0 ~ /^##[[:space:]]+/) exit 0
    print
  }}' "$doc" \\
    | sed -n -E \\
        -e 's/^[[:space:]]*-[[:space:]]*`(scripts\\/[^`]+\\.sh)`[[:space:]]*$/\\1/p' \\
        -e 's/^[[:space:]]*-[[:space:]]*(scripts\\/[^[:space:]]+\\.sh)[[:space:]]*$/\\1/p' \\
    | sed -e '/^[[:space:]]*$/d' \\
    | LC_ALL=C sort -u
  {END}
}}
"""

def norm(s: str) -> str:
    return s.replace("\r\n", "\n")

def main() -> None:
    s = norm(GATE.read_text(encoding="utf-8"))

    if BEGIN in s and END in s:
        print("OK: extractor function already canonical (idempotent).")
        return

    pat = re.compile(r"(?ms)^extract_enforced_by_list\(\)\s*\{\n.*?^\}\n")
    if not pat.search(s):
        raise SystemExit("ERROR: could not locate extract_enforced_by_list() function to replace.")

    # IMPORTANT: use a function replacement so \1 in FN is not treated as a regex backref.
    s2 = pat.sub(lambda _m: FN + "\n", s, count=1)

    GATE.write_text(s2, encoding="utf-8")
    print("OK: replaced extract_enforced_by_list() with canonical capture-group emitter.")

if __name__ == "__main__":
    main()
