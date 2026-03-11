from __future__ import annotations

from pathlib import Path
import re
import sys

DOC = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

ENT_BEGIN = "SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_BEGIN"
ENT_END   = "SV_CREATIVE_SURFACE_REGISTRY_ENTRIES_v1_END"

BLOCK_BEGIN = "# SV_PATCH: CREATIVE_SURFACE_REGISTRY_USAGE_PARSE_ENTRIES_ONLY_v1_BEGIN"
BLOCK_END   = "# SV_PATCH: CREATIVE_SURFACE_REGISTRY_USAGE_PARSE_ENTRIES_ONLY_v1_END"

HELPER = f"""{BLOCK_BEGIN}
# Canonical: registry IDs are read ONLY from the machine-indexed ENTRIES block in:
#   docs/80_indices/ops/Creative_Surface_Registry_v1.0.md
# This avoids false duplicates from prose/markers elsewhere in the doc.
_extract_registry_ids_from_entries_block() {{
  local doc="$1"

  # Require the bounded entries block markers to exist.
  grep -n --fixed-strings "{ENT_BEGIN}" "$doc" >/dev/null
  grep -n --fixed-strings "{ENT_END}" "$doc" >/dev/null

  # Print ONLY "- CREATIVE_SURFACE_*" bullets within the bounded block.
  awk '
    /{ENT_BEGIN}/ {{p=1; next}}
    /{ENT_END}/   {{p=0}}
    p {{print}}
  ' "$doc" | sed -n 's/^[[:space:]]*-[[:space:]]\\(CREATIVE_SURFACE_[A-Z0-9_]*\\)[[:space:]]*$/\\1/p'
}}

# Diagnostics helper: list duplicates in a newline-delimited token stream.
_list_dupes() {{
  sort | uniq -d
}}
{BLOCK_END}
"""

def main() -> int:
    if not DOC.exists():
        print(f"ERROR: missing file: {DOC}", file=sys.stderr)
        return 2

    src = DOC.read_text(encoding="utf-8", errors="replace")

    # 1) Insert/replace helper block right after `set -euo pipefail`.
    if BLOCK_BEGIN in src and BLOCK_END in src:
        pre, rest = src.split(BLOCK_BEGIN, 1)
        _old, post = rest.split(BLOCK_END, 1)
        src2 = pre + HELPER + post
    else:
        m = re.search(r"(?m)^set -euo pipefail[^\n]*\n", src)
        if not m:
            print("ERROR: refused to patch (could not find 'set -euo pipefail' anchor).", file=sys.stderr)
            return 3
        insert_at = m.end()
        src2 = src[:insert_at] + "\n" + HELPER + "\n" + src[insert_at:]

    # 2) Rewrite the registered_ids_raw extraction to use entries-only helper.
    #    Old line pattern includes grep -h -o -E 'CREATIVE_SURFACE_...'
    lines = src2.splitlines(keepends=True)
    out: list[str] = []
    patched_registered = False

    for ln in lines:
        if re.search(r"""registered_ids_raw="\$\(\s*grep\b.*-E\s+'CREATIVE_SURFACE_\[A-Z0-9_]\+\*?""", ln) or (
            "registered_ids_raw" in ln and "grep -h -o -E 'CREATIVE_SURFACE_" in ln
        ):
            out.append('registered_ids_raw="$(_extract_registry_ids_from_entries_block "$registry_doc" || true)"\n')
            patched_registered = True
            continue
        out.append(ln)

    if not patched_registered:
        # Fallback: find the exact existing assignment and replace it more simply.
        out2: list[str] = []
        for ln in out:
            if ln.strip().startswith("registered_ids_raw=") and "CREATIVE_SURFACE_" in ln and "$registry_doc" in ln:
                out2.append('registered_ids_raw="$(_extract_registry_ids_from_entries_block "$registry_doc" || true)"\n')
                patched_registered = True
            else:
                out2.append(ln)
        out = out2

    if not patched_registered:
        print("ERROR: refused to patch (could not locate registered_ids_raw extraction line).", file=sys.stderr)
        print(f"File: {DOC}", file=sys.stderr)
        return 4

    newer = "".join(out)

    # 3) Improve the duplicate error branch to print actual dupes.
    # Insert dupes printing immediately before the `exit 1` that follows the duplicate message,
    # but only if we haven't already added a "Duplicates:" line.
    if 'echo "Duplicates:"' not in newer:
        pat = r'(?ms)(echo\s+"ERROR:\s*duplicate CREATIVE_SURFACE_\*\s*tokens in registry doc".*?\n)(\s*exit\s+1\s*\n)'
        repl = (
            r'\1'
            r'echo "Duplicates:" >&2\n'
            r'printf "%s\n" "$registered_ids_raw" | sed "/^$/d" | _list_dupes | sed "s/^/ - /" >&2\n'
            r'\2'
        )
        newer = re.sub(pat, repl, newer, count=1)

    if newer != src:
        DOC.write_text(newer, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
