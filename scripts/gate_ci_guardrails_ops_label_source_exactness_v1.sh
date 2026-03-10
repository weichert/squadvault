#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 - <<'PY_CHECK'
from pathlib import Path

repo = Path(".")
prove_path = repo / "scripts" / "prove_ci.sh"
labels_tsv = repo / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
cluster_tsv = repo / "docs" / "80_indices" / "ops" / "CI_Guardrails_Ops_Cluster_Order_v1.tsv"
index_doc = repo / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

def normalize_gate_path(token: str) -> str | None:
    token = token.strip().strip('"').strip("'")
    if token.startswith("./"):
        token = token[2:]
    if token.startswith("bash "):
        parts = token.split()
        if len(parts) >= 2:
            token = parts[1]
    marker = "/scripts/gate_"
    if marker in token and token.endswith(".sh"):
        token = token[token.index("scripts/"):]
    if token.startswith("scripts/gate_") and token.endswith(".sh"):
        return token
    return None

def read_labels_map(path: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        gate_path, label = line.split("\t", 1)
        labels[gate_path] = label
    return labels

def read_cluster_order(path: Path) -> list[str]:
    ordered: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        gate_path, _label = line.split("\t", 1)
        ordered.append(gate_path)
    return ordered

def extract_executed_gate_paths(prove_text: str) -> list[str]:
    paths: list[str] = []
    for raw in prove_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        normalized = normalize_gate_path(line)
        if normalized is not None:
            paths.append(normalized)
        for part in line.replace("=", " ").split():
            normalized = normalize_gate_path(part)
            if normalized is not None:
                paths.append(normalized)
    return paths

def ordered_paths_from_prove_text(prove_text: str, ordered_cluster: list[str]) -> list[str]:
    executed = extract_executed_gate_paths(prove_text)
    executed_set = set(executed)

    missing_cluster = [path for path in ordered_cluster if path not in executed_set]
    if missing_cluster:
        raise SystemExit(
            "ERROR: missing ordered Ops cluster gate(s) from scripts/prove_ci.sh:\n- "
            + "\n- ".join(missing_cluster)
        )

    ordered: list[str] = []
    seen: set[str] = set()

    for path in ordered_cluster:
        if path not in seen:
            ordered.append(path)
            seen.add(path)

    for path in executed:
        if path not in seen:
            ordered.append(path)
            seen.add(path)

    return ordered

def extract_rendered_bullets(index_text: str) -> list[str]:
    b = index_text.find(begin)
    e = index_text.find(end)
    if b < 0 or e < 0 or b >= e:
        raise SystemExit("ERROR: could not locate bounded Ops section in index doc")
    inner = index_text[b + len(begin):e]
    bullets: list[str] = []
    for raw in inner.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith("- scripts/"):
            bullets.append(stripped)
    return bullets

labels = read_labels_map(labels_tsv)
cluster_order = read_cluster_order(cluster_tsv)

missing_cluster_labels = [path for path in cluster_order if path not in labels]
if missing_cluster_labels:
    raise SystemExit(
        "ERROR: missing canonical labels for cluster-order path(s):\n- "
        + "\n- ".join(missing_cluster_labels)
    )

prove_text = prove_path.read_text(encoding="utf-8")
ordered_paths = ordered_paths_from_prove_text(prove_text, cluster_order)

missing_render_labels = [path for path in ordered_paths if path not in labels]
if missing_render_labels:
    raise SystemExit(
        "ERROR: missing canonical labels for rendered path(s):\n- "
        + "\n- ".join(missing_render_labels)
    )

expected_bullets = [f"- {path} — {labels[path]}" for path in ordered_paths]
actual_bullets = extract_rendered_bullets(index_doc.read_text(encoding="utf-8"))

if actual_bullets != expected_bullets:
    raise SystemExit(
        "ERROR: rendered Ops bounded block does not match canonical label source.\n\n"
        "Expected bullets:\n- " + "\n- ".join(expected_bullets) + "\n\n"
        "Actual bullets:\n- " + "\n- ".join(actual_bullets)
    )

print("OK: CI Guardrails Ops label source exactness (v1)")
PY_CHECK
