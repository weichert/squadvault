#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

cd "$REPO_ROOT"

"$REPO_ROOT/scripts/py" - <<'GATE_PY'
from __future__ import annotations

from pathlib import Path
import re
import sys

repo = Path.cwd()
tsv_path = repo / "docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv"
index_path = repo / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

index_begin = "SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN"
index_end = "SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END"

def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)

if not tsv_path.is_file():
    die(f"missing file: {tsv_path}")

if not index_path.is_file():
    die(f"missing file: {index_path}")

tsv_rows = {}
for raw in tsv_path.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line:
        continue
    if line.startswith("#"):
        continue
    cols = raw.split("\t")
    if len(cols) < 2:
        continue
    script_path = cols[0].strip()
    desc = cols[-1].strip()
    if not script_path.startswith("scripts/gate_"):
        continue
    if not script_path.endswith(".sh"):
        continue
    if script_path in tsv_rows and tsv_rows[script_path] != desc:
        die(f"duplicate TSV entry with conflicting description: {script_path}")
    tsv_rows[script_path] = desc

index_text = index_path.read_text(encoding="utf-8")
pattern = re.compile(
    r"(?ms)^.*?"
    + re.escape(index_begin)
    + r"\n(?P<body>.*?)\n.*?"
    + re.escape(index_end)
    + r".*$"
)
match = pattern.search(index_text)
if not match:
    die("missing CI guardrails entrypoints bounded section in Ops index")

index_rows = {}
for raw in match.group("body").splitlines():
    line = raw.strip()
    if not line.startswith("- "):
        continue
    found = re.match(r"^-\s+`?(scripts/gate_[^`\s]+\.sh)`?\s*(?:—|-|:)\s*(.+?)\s*$", line)
    if not found:
        continue
    script_path = found.group(1).strip()
    desc = found.group(2).strip()
    if script_path in index_rows and index_rows[script_path] != desc:
        die(f"duplicate Ops index entry with conflicting description: {script_path}")
    index_rows[script_path] = desc

errors = []

for script_path in sorted(set(tsv_rows) - set(index_rows)):
    errors.append(f"TSV entry missing from Ops index: {script_path}")

for script_path in sorted(set(index_rows) - set(tsv_rows)):
    errors.append(f"Ops index entry missing from TSV registry: {script_path}")

for script_path in sorted(set(tsv_rows) & set(index_rows)):
    if tsv_rows[script_path] != index_rows[script_path]:
        errors.append(
            "description mismatch for "
            + script_path
            + " | TSV='"
            + tsv_rows[script_path]
            + "' | INDEX='"
            + index_rows[script_path]
            + "'"
        )

for script_path in sorted(tsv_rows):
    if not (repo / script_path).is_file():
        errors.append(f"TSV script path missing on disk: {script_path}")

if errors:
    for err in errors:
        print(err, file=sys.stderr)
    raise SystemExit(1)

print("OK: CI Guardrails ops label registry parity (v1)")
GATE_PY
