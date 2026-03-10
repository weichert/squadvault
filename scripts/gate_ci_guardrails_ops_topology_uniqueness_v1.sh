#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 - <<'PY_CHECK'
from collections import Counter
from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
TSV = Path("docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv")
PROVE = Path("scripts/prove_ci.sh")
CLUSTER = Path("scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh")

INDEX_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
INDEX_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"


def fail(msg: str) -> None:
    raise SystemExit(msg)


def duplicates(seq: list[str]) -> list[str]:
    counts = Counter(seq)
    return [item for item, count in counts.items() if count > 1]


def parse_index_paths() -> list[str]:
    text = INDEX.read_text(encoding="utf-8")
    if INDEX_BEGIN not in text or INDEX_END not in text:
        fail("ERROR: missing CI Guardrails Ops entrypoint markers in Ops index")
    block = text.split(INDEX_BEGIN, 1)[1].split(INDEX_END, 1)[0]
    paths: list[str] = []
    for raw in block.splitlines():
        stripped = raw.strip()
        if stripped.startswith("- scripts/"):
            if " — " not in stripped:
                fail(f"ERROR: malformed Ops index entry line: {stripped}")
            paths.append(stripped.split(" — ", 1)[0][2:].strip())
    return paths


def parse_tsv_paths() -> list[str]:
    paths: list[str] = []
    for lineno, raw in enumerate(TSV.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        parts = raw.split("\t")
        if len(parts) != 2:
            fail(f"ERROR: malformed TSV row at line {lineno}: {raw}")
        paths.append(parts[0].strip())
    return paths


def parse_prove_ops_lines() -> list[str]:
    lines: list[str] = []
    for raw in PROVE.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped.startswith("bash scripts/gate_ci_guardrails_ops_"):
            lines.append(stripped)
    return lines


def parse_cluster_expected_lines() -> list[str]:
    lines = CLUSTER.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    in_list = False
    for raw in lines:
        stripped = raw.strip()
        if stripped == "expected_lines = [":
            in_list = True
            continue
        if in_list and stripped == "]":
            break
        if in_list:
            if not stripped.startswith('"bash scripts/') or not stripped.endswith('",'):
                fail(f"ERROR: malformed expected_lines entry in cluster canonical gate: {stripped}")
            out.append(stripped[1:-2])
    return out


prove_dups = duplicates(parse_prove_ops_lines())
if prove_dups:
    fail("ERROR: duplicate Ops guardrails invocations in scripts/prove_ci.sh:\n- " + "\n- ".join(prove_dups))

index_dups = duplicates(parse_index_paths())
if index_dups:
    fail("ERROR: duplicate entries in Ops index bounded section:\n- " + "\n- ".join(index_dups))

tsv_dups = duplicates(parse_tsv_paths())
if tsv_dups:
    fail("ERROR: duplicate entries in TSV label registry:\n- " + "\n- ".join(tsv_dups))

cluster_dups = duplicates(parse_cluster_expected_lines())
if cluster_dups:
    fail("ERROR: duplicate entries in cluster canonical expected block:\n- " + "\n- ".join(cluster_dups))

print("OK: CI Guardrails Ops topology uniqueness (v1)")
PY_CHECK
