from __future__ import annotations

from pathlib import Path
import re

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

NEEDLE = "scripts/prove_ci_creative_sharepack_if_available_v1.sh"
BULLET = f"- {NEEDLE} — Creative sharepack determinism (conditional) proof (v1)"

def main() -> None:
    text = REG.read_text(encoding="utf-8")

    if NEEDLE in text:
        print("OK: CI proof surface registry already contains creative sharepack proof (noop)")
        return

    # Prefer inserting under an obvious proof-runner list heading if present.
    # We accept a few common headings to avoid guessing.
    headings = [
        r"^##[ \t]+Proof runners\b.*$",
        r"^##[ \t]+Proof surfaces\b.*$",
        r"^##[ \t]+CI proof runners\b.*$",
        r"^##[ \t]+Registry\b.*$",
    ]

    for hpat in headings:
        m = re.search(hpat, text, flags=re.M)
        if not m:
            continue

        # Insert after the heading block (skip any immediate blank line)
        ins = text.find("\n", m.end())
        if ins == -1:
            ins = len(text)
        else:
            ins += 1

        # If next line is blank, keep a single blank line before bullets
        # then insert bullet.
        new = text[:ins]
        if not new.endswith("\n"):
            new += "\n"
        # Avoid double-blank spam
        if not new.endswith("\n\n"):
            new += "\n"

        new = new + BULLET + "\n" + text[ins:]
        REG.write_text(new, encoding="utf-8")
        print("OK: added creative sharepack proof runner to CI proof surface registry (v1)")
        return

    raise SystemExit(
        "ERR: could not find a known registry heading to insert under; refusing to guess. "
        "Open docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md and add the bullet manually."
    )

if __name__ == "__main__":
    main()
