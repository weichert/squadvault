from __future__ import annotations

from pathlib import Path
import stat

REPO = Path(__file__).resolve().parents[1]
RENDER = REPO / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"

RENDER_TEXT = r'''from __future__ import annotations

from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
PROVE_CI = REPO / "scripts" / "prove_ci.sh"
LABELS_TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
CLUSTER_ORDER_TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Ops_Cluster_Order_v1.tsv"

BEGIN_MARKER = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END_MARKER = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"


def _normalize_gate_path(token: str) -> str | None:
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


def _read_labels_map(labels_path: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    for raw in labels_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        path, label = line.split("\t", 1)
        labels[path] = label
    return labels


def _read_cluster_order(cluster_path: Path) -> list[str]:
    ordered: list[str] = []
    for raw in cluster_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        path, _label = line.split("\t", 1)
        ordered.append(path)
    return ordered


def _extract_executed_gate_paths(prove_text: str) -> list[str]:
    paths: list[str] = []
    for raw in prove_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        normalized = _normalize_gate_path(line)
        if normalized is not None:
            paths.append(normalized)

        for part in line.replace("=", " ").split():
            normalized = _normalize_gate_path(part)
            if normalized is not None:
                paths.append(normalized)

    return paths


def _ordered_paths_from_prove_text(prove_text: str, ordered_cluster: list[str]) -> list[str]:
    executed = _extract_executed_gate_paths(prove_text)
    executed_set = set(executed)

    missing_cluster = [path for path in ordered_cluster if path not in executed_set]
    if missing_cluster:
        raise RuntimeError(
            "missing ordered Ops cluster gate(s) from scripts/prove_ci.sh:\n- "
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


def render_block_from_prove_text(
    prove_text: str,
    labels_path: Path = LABELS_TSV,
    cluster_path: Path = CLUSTER_ORDER_TSV,
) -> str:
    labels = _read_labels_map(labels_path)
    ordered_cluster = _read_cluster_order(cluster_path)
    ordered_paths = _ordered_paths_from_prove_text(prove_text, ordered_cluster)

    missing_labels = [path for path in ordered_paths if path not in labels]
    if missing_labels:
        raise RuntimeError(
            "missing canonical CI guardrail labels for:\n- "
            + "\n- ".join(missing_labels)
            + "\nAdd TSV entries to docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv."
        )

    bullets = [f"- {path} — {labels[path]}" for path in ordered_paths]

    lines = [
        BEGIN_MARKER,
        "# CI Guardrails Ops Entrypoints",
        "",
        "# - This section is enforced by scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
        "# - Canonical Ops cluster order source: docs/80_indices/ops/CI_Guardrails_Ops_Cluster_Order_v1.tsv",
        "",
        *bullets,
        END_MARKER,
        "",
    ]
    return "\n".join(lines)


def render_block_from_prove_path(prove_path: Path = PROVE_CI) -> str:
    return render_block_from_prove_text(prove_path.read_text(encoding="utf-8"))


def main() -> int:
    sys.stdout.write(render_block_from_prove_path(PROVE_CI))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

def write_if_changed(path: Path, text: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True

def ensure_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def main() -> int:
    changed = False

    if write_if_changed(RENDER, RENDER_TEXT):
        changed = True

    ensure_executable(RENDER)

    if changed:
        print("OK: renderer now captures gate path assignments (v1)")
    else:
        print("OK: renderer already captures gate path assignments (noop)")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
