from __future__ import annotations
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

MARKER = "CI_Proof_Surface_Registry_v1.0.md"

BLOCK = """\
## Proof Surface

- **CI Proof Surface Registry (v1.0)**  
  Canonical, frozen list of all proof runners invoked by CI.  
  → docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md
"""

HEADER = """\
# CI Guardrails — Index (v1.0)

This index provides discoverability for CI-enforced operational guardrails.
"""

def main() -> None:
  INDEX.parent.mkdir(parents=True, exist_ok=True)

  if not INDEX.exists():
    INDEX.write_text(HEADER + "\n\n" + BLOCK + "\n", encoding="utf-8")
    print("OK: CI guardrails index created and proof surface link added (v2)")
    return

  text = INDEX.read_text(encoding="utf-8")

  if MARKER in text:
    print("OK: CI index already links proof surface registry (no-op)")
    return

  INDEX.write_text(text.rstrip() + "\n\n" + BLOCK + "\n", encoding="utf-8")
  print("OK: CI guardrails index updated (proof surface link added)")

if __name__ == "__main__":
  main()
