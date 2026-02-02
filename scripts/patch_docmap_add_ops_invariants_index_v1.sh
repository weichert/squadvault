#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docmap add ops invariants index reference (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

DOC="docs/canonical/Documentation_Map_and_Canonical_References.md"
test -f "${DOC}" || { echo "ERROR: missing ${DOC}" 1>&2; exit 1; }

python="${PYTHON:-python3}"
if ! command -v "${python}" >/dev/null 2>&1; then
  python="python"
fi

"${python}" - <<'PY'
from pathlib import Path

doc = Path("docs/canonical/Documentation_Map_and_Canonical_References.md")
txt = doc.read_text()

needle = "docs/ops/invariants/INDEX_v1.0.md"
if needle in txt:
    print(f"OK: already referenced: {needle}")
    raise SystemExit(0)

# Prefer inserting near ops/guardrails/CI language if present.
anchors = [
    "## Ops",
    "## Operations",
    "## Operational",
    "## CI",
    "## Guardrails",
    "## Governance",
]

insert_block = "\n".join([
    "",
    "## Ops Invariants",
    "",
    "- **Ops Invariants Index (v1.0)**",
    f"  `{needle}`",
    "",
])

# Try to insert before the first matching anchor AFTER it, by appending a small section at end if uncertain.
inserted = False
for a in anchors:
    idx = txt.find(a)
    if idx != -1:
        # Insert just before the anchor header we found (keeps section ordering stable).
        txt = txt[:idx] + insert_block + txt[idx:]
        inserted = True
        break

if not inserted:
    # Append at end (minimal, safe).
    if not txt.endswith("\n"):
        txt += "\n"
    txt += insert_block
    inserted = True

doc.write_text(txt)
print(f"OK: patched {doc}")
PY

echo "OK"
