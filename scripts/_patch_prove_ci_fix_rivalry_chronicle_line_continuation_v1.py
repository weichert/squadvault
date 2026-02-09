from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

# We specifically want to remove a blank line *immediately after* the prove invocation line that ends with "\"
# Example bad:
#   ...prove_rivalry_chronicle_end_to_end_v1.sh \
#
#   --db "${WORK_DB}" \
#
# Make it:
#   ...prove_rivalry_chronicle_end_to_end_v1.sh \
#   --db "${WORK_DB}" \

ANCHOR_RE = re.compile(
    r'(bash\s+scripts/prove_rivalry_chronicle_end_to_end_v1\.sh\s+\\\s*\n)\n(\s*--db\s+)'
)

def main() -> None:
    txt = PROVE.read_text(encoding="utf-8")

    new, n = ANCHOR_RE.subn(r"\1\2", txt)
    if n == 0:
        # If already canonical, no-op (idempotent)
        return

    PROVE.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    main()
