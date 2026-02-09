from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_rivalry_chronicle_contract_linkage_v1.sh")
PROVE_CI = Path("scripts/prove_ci.sh")

PROVE_RC = "scripts/prove_rivalry_chronicle_end_to_end_v1.sh"
CONTRACT = "docs/contracts/rivalry_chronicle_output_contract_v1.md"

GATE_TEXT = f"""#!/usr/bin/env bash
set -euo pipefail

echo "==> Gate: Rivalry Chronicle contract linkage (v1)"

REPO_ROOT="$(cd "$(dirname "${{BASH_SOURCE[0]}}")/.." && pwd)"
cd "${{REPO_ROOT}}"

PROVE="{PROVE_RC}"
CONTRACT="{CONTRACT}"

if [[ ! -f "${{PROVE}}" ]]; then
  echo "ERROR: missing prove script: ${{PROVE}}" >&2
  exit 1
fi

if ! grep -q "{CONTRACT}" "${{PROVE}}"; then
  echo "ERROR: prove script does not reference contract source-of-truth path: {CONTRACT}" >&2
  echo "       expected exact string in ${{PROVE}}" >&2
  exit 1
fi

if [[ ! -f "${{CONTRACT}}" ]]; then
  echo "ERROR: contract doc missing at ${{CONTRACT}}" >&2
  exit 1
fi

echo "OK: Rivalry Chronicle prove script links to contract doc (v1)"
"""

ANCHOR = '# SV_GATE: contracts_index_discoverability (v1) begin'
INSERT_BLOCK = """\
# SV_GATE: rivalry_chronicle_contract_linkage (v1) begin
echo "==> Gate: Rivalry Chronicle contract linkage (v1)"
bash scripts/gate_rivalry_chronicle_contract_linkage_v1.sh
# SV_GATE: rivalry_chronicle_contract_linkage (v1) end

"""

def main() -> None:
    changed = False

    # write gate file
    if GATE.exists():
        cur = GATE.read_text(encoding="utf-8")
        if cur != GATE_TEXT:
            GATE.write_text(GATE_TEXT, encoding="utf-8")
            changed = True
    else:
        GATE.write_text(GATE_TEXT, encoding="utf-8")
        changed = True

    if not PROVE_CI.exists():
        raise SystemExit(f"REFUSE: missing {PROVE_CI}")

    text = PROVE_CI.read_text(encoding="utf-8")

    if "bash scripts/gate_rivalry_chronicle_contract_linkage_v1.sh" not in text:
        if ANCHOR not in text:
            raise SystemExit(f"REFUSE: anchor missing in {PROVE_CI}: {ANCHOR}")
        text = text.replace(ANCHOR, INSERT_BLOCK + ANCHOR, 1)
        PROVE_CI.write_text(text, encoding="utf-8")
        changed = True

    if not changed:
        print("OK: Rivalry Chronicle contract linkage gate already canonical + wired (v1 idempotent).")
    else:
        print("OK: Rivalry Chronicle contract linkage gate created/wired (v1).")

if __name__ == "__main__":
    main()
