#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import re

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BUNDLE_LINE = "- `scripts/ops_bundle_ci_docs_hardening_v1.sh` — CI + docs hardening sweep (idempotent; runs via `scripts/ops_orchestrate.sh`)."
SECTION_HDR = "## Ops Bundles"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    text = TARGET.read_text(encoding="utf-8")

    # Idempotency: if the bundle is already referenced anywhere, no-op.
    if "ops_bundle_ci_docs_hardening_v1.sh" in text:
        print("OK: CI_Guardrails_Index already references ops bundle (v1 no-op).")
        return

    if not text.endswith("\n"):
        text += "\n"

    if SECTION_HDR not in text:
        # Minimal append: add a small section at the end.
        text += "\n" + SECTION_HDR + "\n\n" + BUNDLE_LINE + "\n"
        TARGET.write_text(text, encoding="utf-8")
        print("OK: appended Ops Bundles section + bundle pointer to CI_Guardrails_Index (v1).")
        return

    # Section exists: insert the bullet right after the header line (keeping existing content).
    pattern = re.compile(r"^## Ops Bundles\s*$", re.MULTILINE)
    m = pattern.search(text)
    if not m:
        raise SystemExit("ERROR: could not locate Ops Bundles header (unexpected)")

    insert_at = m.end()

    # Ensure there's a blank line after header, then the bullet.
    # Insert like: "\n\n- `...`\n" if needed.
    after = text[insert_at:]
    prefix = "\n"
    if not after.startswith("\n"):
        prefix = "\n\n"

    new_text = text[:insert_at] + prefix + "\n" + BUNDLE_LINE + "\n" + text[insert_at:]
    TARGET.write_text(new_text, encoding="utf-8")
    print("OK: inserted ops bundle pointer under Ops Bundles in CI_Guardrails_Index (v1).")

if __name__ == "__main__":
    main()
