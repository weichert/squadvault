from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

NEEDLE = "bash scripts/prove_docs_integrity_v1.sh\n"

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"missing canonical file: {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    if NEEDLE not in text:
        # already removed (idempotent)
        return

    # Refuse to guess if it appears more than once.
    if text.count(NEEDLE) != 1:
        raise SystemExit("expected exactly one standalone prove_docs_integrity_v1.sh call")

    PROVE.write_text(text.replace(NEEDLE, ""), encoding="utf-8")

if __name__ == "__main__":
    main()
