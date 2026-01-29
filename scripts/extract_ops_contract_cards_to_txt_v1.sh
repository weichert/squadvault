#!/usr/bin/env bash
set -euo pipefail
echo "=== Extract: ops contract cards docx -> txt (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUT_DIR="docs/30_contract_cards/ops/_extracted_txt"
mkdir -p "${OUT_DIR}"

python="${PYTHON:-python}"
$python - <<'PY'
from pathlib import Path
from docx import Document

root = Path("docs/30_contract_cards/ops")
out = root / "_extracted_txt"
out.mkdir(parents=True, exist_ok=True)

paths = [
    root / "APPROVAL_AUTHORITY_Contract_Card_v1.0.docx",
    root / "CONTRACT_VALIDATION_STRATEGY_Contract_Card_v1.0.docx",
    root / "EAL_CALIBRATION_Contract_Card_v1.0.docx",
    root / "TONE_ENGINE_Contract_Card_v1.0.docx",
    root / "VERSION_PRESENTATION_NAVIGATION_Contract_Card_v1.0.docx",
]

for p in paths:
    doc = Document(str(p))
    txt = "\n".join((para.text or "").rstrip() for para in doc.paragraphs)
    out_path = out / (p.stem + ".txt")
    out_path.write_text(txt.strip() + "\n", encoding="utf-8")
    print(f"OK: {p} -> {out_path}")
PY
