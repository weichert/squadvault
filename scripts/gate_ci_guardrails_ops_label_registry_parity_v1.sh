#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

cd "$REPO_ROOT"

"$REPO_ROOT/scripts/py" - <<'LABEL_REGISTRY_PARITY_PY'
from __future__ import annotations

from pathlib import Path
import sys

repo = Path.cwd()
prove_path = repo / "scripts/prove_ci.sh"
index_path = repo / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
tsv_path = repo / "docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv"

index_begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
index_end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"
cluster_start = "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh"
cluster_end = "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh"

def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)

def parse_cluster(text: str) -> list[str]:
    started = False
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if line == cluster_start:
            started = True
        if started and line.startswith("bash scripts/gate_ci_guardrails_ops_"):
            out.append(line.replace("bash ", "", 1))
        if started and line == cluster_end:
            break
    if not out:
        die("could not locate ops guardrails cluster in scripts/prove_ci.sh")
    return out

def parse_index(text: str) -> dict[str, str]:
    if index_begin not in text or index_end not in text:
        die("missing CI guardrails entrypoints bounded section in Ops index")
    _, rest = text.split(index_begin, 1)
    body, _ = rest.split(index_end, 1)
    rows = {}
    for raw in body.strip("\n").splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        if " — " not in line:
            continue
        left, desc = line[2:].split(" — ", 1)
        script_path = left.strip().strip("`")
        desc = desc.strip()
        if not script_path.startswith("scripts/gate_ci_guardrails_ops_"):
            continue
        if script_path in rows and rows[script_path] != desc:
            die(f"duplicate Ops index entry with conflicting description: {script_path}")
        rows[script_path] = desc
    return rows

def parse_tsv(text: str) -> dict[str, str]:
    rows = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cols = raw.split("\t")
        if len(cols) < 2:
            continue
        script_path = cols[0].strip()
        desc = cols[-1].strip()
        if not script_path.startswith("scripts/gate_ci_guardrails_ops_"):
            continue
        if script_path in rows and rows[script_path] != desc:
            die(f"duplicate TSV entry with conflicting description: {script_path}")
        rows[script_path] = desc
    return rows

prove_text = prove_path.read_text(encoding="utf-8")
index_text = index_path.read_text(encoding="utf-8")
tsv_text = tsv_path.read_text(encoding="utf-8")

cluster_rows = parse_cluster(prove_text)
index_rows = parse_index(index_text)
tsv_rows = parse_tsv(tsv_text)

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

for script_path in sorted(set(cluster_rows) - set(tsv_rows)):
    errors.append(f"Ops cluster script missing from TSV registry: {script_path}")

for script_path in sorted(set(cluster_rows) - set(index_rows)):
    errors.append(f"Ops cluster script missing from Ops index: {script_path}")

if errors:
    for err in errors:
        print(err, file=sys.stderr)
    raise SystemExit(1)

print("OK: CI Guardrails ops label registry parity (v1)")
LABEL_REGISTRY_PARITY_PY
