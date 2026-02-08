from __future__ import annotations

from pathlib import Path
import os

DOC = Path(os.environ["SV_CI_INDEX_DOC"])

BEGIN = "<!-- PROOF_SUITE_COMPLETENESS_GATE_v1_BEGIN -->"
END = "<!-- PROOF_SUITE_COMPLETENESS_GATE_v1_END -->"

BLOCK = f"""\
{BEGIN}
### Proof suite completeness gate (v1)

**Invariant (fail-closed):** every `scripts/prove_*.sh` proof runner **must** be referenced in the canonical Proof Surface Registry, and the registry list must match the filesystem list **exactly**.

- Gate: `scripts/gate_proof_suite_completeness_v1.sh`
- Wired by: `scripts/prove_ci.sh` (inserted under `SV_ANCHOR: docs_gates (v1)`)
- Registry: `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md`
- Purpose: prevents proof coverage drift (new/removed proof runner scripts that CI would otherwise miss)

{END}
"""

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: missing {DOC}")

    text = DOC.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        return

    patched = text.rstrip() + "\n\n" + BLOCK + "\n"
    DOC.write_text(patched, encoding="utf-8")

if __name__ == "__main__":
    main()
