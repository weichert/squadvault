from __future__ import annotations
from pathlib import Path

TARGET = Path("docs/process/rules_of_engagement.md")

SNIPPET = """\
## Docs + CI Mutation Policy (Enforced)

All changes that modify `docs/` or CI guardrails must be implemented via:
- a **versioned patcher** (`scripts/_patch_*.py`), and
- a **versioned wrapper** (`scripts/patch_*.sh`).

Manual edits are permitted only for emergency repair and must be followed by a patcher+wrapper retrofit.
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target file: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")
    if "Docs + CI Mutation Policy (Enforced)" in s:
        print("OK: policy already present")
        return

    TARGET.write_text(s.rstrip() + "\n\n" + SNIPPET + "\n", encoding="utf-8")
    print("OK: appended Docs+CI mutation policy to rules_of_engagement")

if __name__ == "__main__":
    main()
