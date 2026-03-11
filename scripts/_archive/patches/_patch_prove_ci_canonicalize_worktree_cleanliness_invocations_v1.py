from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not PROVE.exists():
        die(f"missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    # Replace non-canonical direct invocations with canonical bash form
    new = re.sub(
        r'(?m)^(?P<prefix>\s*)scripts/gate_worktree_cleanliness_v1\.sh(?=\s)',
        r'\g<prefix>bash scripts/gate_worktree_cleanliness_v1.sh',
        text,
    )

    if new != text:
        PROVE.write_text(new, encoding="utf-8")

if __name__ == "__main__":
    main()
