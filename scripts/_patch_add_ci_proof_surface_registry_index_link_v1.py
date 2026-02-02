from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

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
    INDEX.write_text(HEADER + "\n" + BLOCK + "\n", encoding="utf-8")
    return

  text = INDEX.read_text(encoding="utf-8")
  if "CI_Proof_Surface_Registry_v1.0.md" in text:
    return  # idempotent

  INDEX.write_text(text.rstrip() + "\n\n" + BLOCK + "\n", encoding="utf-8")

if __name__ == "__main__":
  main()
