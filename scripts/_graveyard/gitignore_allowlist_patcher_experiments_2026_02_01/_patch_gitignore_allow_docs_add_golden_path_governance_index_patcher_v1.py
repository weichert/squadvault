from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")

NEEDLE = "!scripts/_patch_docs_add_golden_path_governance_index_v1.py\n"
ANCHOR = "# Canonical allowlist only:\n"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    txt = TARGET.read_text(encoding="utf-8")

    if NEEDLE in txt:
        print("OK: already allowlisted (no-op)")
        return

    if ANCHOR not in txt:
        raise SystemExit("ERROR: could not locate canonical allowlist anchor in .gitignore")

    head, rest = txt.split(ANCHOR, 1)
    out = head + ANCHOR + NEEDLE + rest
    TARGET.write_text(out, encoding="utf-8")
    print("OK: inserted allowlist entry into canonical allowlist block")

if __name__ == "__main__":
    main()
