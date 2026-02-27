from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("scripts/gate_prove_ci_structure_canonical_v1.sh")

# Replace the whole grep|sed extractor block with an awk field-scanner extractor.
PATTERN = re.compile(
    r"""(?ms)
^# Extract gate invocation paths from prove_ci\.sh\.\n
.*?
> "\$paths_file" \|\| true\n
""",
)

REPLACEMENT = """# Extract gate invocation paths from prove_ci.sh (BSD/macOS-safe).
# We scan whitespace-delimited fields and capture any token matching:
#   (./)?scripts/gate_*.sh
# Then normalize ./scripts/... -> scripts/...
awk '
  {
    for (i = 1; i <= NF; i++) {
      if ($i ~ /^(\\.\\/)?scripts\\/gate_[^[:space:]]+\\.sh$/) {
        gsub(/^\\.\\//, "", $i)
        print $i
      }
    }
  }
' "$PROVE" > "$paths_file" || true
"""

def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: missing target: {TARGET}", file=sys.stderr)
        return 2

    src = TARGET.read_text(encoding="utf-8")

    if REPLACEMENT in src:
        return 0

    m = PATTERN.search(src)
    if not m:
        print("ERROR: refused to patch (could not locate extractor block).", file=sys.stderr)
        return 3

    new_src = src[: m.start()] + REPLACEMENT + src[m.end() :]
    TARGET.write_text(new_src, encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
