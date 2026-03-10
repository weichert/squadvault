from __future__ import annotations

from pathlib import Path
import os
import stat

REPO = Path(__file__).resolve().parents[1]

PROVE = REPO / "scripts" / "prove_ci.sh"
INDEX = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
CLUSTER = REPO / "scripts" / "gate_ci_guardrails_ops_cluster_canonical_v1.sh"
GATE = REPO / "scripts" / "gate_ci_guardrails_ops_label_registry_parity_v1.sh"
ADD_PATCHER = REPO / "scripts" / "_patch_add_gate_ci_guardrails_ops_label_registry_parity_v1.py"
ADD_WRAPPER = REPO / "scripts" / "patch_add_gate_ci_guardrails_ops_label_registry_parity_v1.sh"

TARGET = "scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh"
TARGET_DESC = "Ensures TSV registry ↔ Ops index ↔ gate scripts stay perfectly synchronized."
TARGET_TSV = TARGET + "\t" + TARGET_DESC

INDEX_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
INDEX_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

CLUSTER_LINES = [
    "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
    "bash scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh",
    "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
]

GATE_TEXT = "\n".join(
    [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        'REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"',
        "",
        'cd "$REPO_ROOT"',
        "",
        '"$REPO_ROOT/scripts/py" - <<'"'"'LABEL_REGISTRY_PARITY_PY'"'"'',
        "from __future__ import annotations",
        "",
        "from pathlib import Path",
        "import sys",
        "",
        "repo = Path.cwd()",
        'prove_path = repo / "scripts/prove_ci.sh"',
        'index_path = repo / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"',
        'tsv_path = repo / "docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv"',
        "",
        'index_begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"',
        'index_end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"',
        'cluster_start = "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh"',
        'cluster_end = "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh"',
        "",
        "def die(msg: str) -> None:",
        "    print(msg, file=sys.stderr)",
        "    raise SystemExit(1)",
        "",
        "def parse_cluster(text: str) -> list[str]:",
        "    started = False",
        "    out = []",
        "    for raw in text.splitlines():",
        "        line = raw.strip()",
        "        if line == cluster_start:",
        "            started = True",
        '        if started and line.startswith("bash scripts/gate_ci_guardrails_ops_"):',
        '            out.append(line.replace("bash ", "", 1))',
        "        if started and line == cluster_end:",
        "            break",
        "    if not out:",
        '        die("could not locate ops guardrails cluster in scripts/prove_ci.sh")',
        "    return out",
        "",
        "def parse_index(text: str) -> dict[str, str]:",
        "    if index_begin not in text or index_end not in text:",
        '        die("missing CI guardrails entrypoints bounded section in Ops index")',
        "    _, rest = text.split(index_begin, 1)",
        "    body, _ = rest.split(index_end, 1)",
        "    rows = {}",
        '    for raw in body.strip("\\n").splitlines():',
        "        line = raw.strip()",
        '        if not line.startswith("- "):',
        "            continue",
        '        if " — " not in line:',
        "            continue",
        '        left, desc = line[2:].split(" — ", 1)',
        '        script_path = left.strip().strip("`")',
        "        desc = desc.strip()",
        '        if not script_path.startswith("scripts/gate_ci_guardrails_ops_"):',
        "            continue",
        "        if script_path in rows and rows[script_path] != desc:",
        '            die(f"duplicate Ops index entry with conflicting description: {script_path}")',
        "        rows[script_path] = desc",
        "    return rows",
        "",
        "def parse_tsv(text: str) -> dict[str, str]:",
        "    rows = {}",
        "    for raw in text.splitlines():",
        "        line = raw.strip()",
        '        if not line or line.startswith("#"):',
        "            continue",
        '        cols = raw.split("\\t")',
        "        if len(cols) < 2:",
        "            continue",
        "        script_path = cols[0].strip()",
        "        desc = cols[-1].strip()",
        '        if not script_path.startswith("scripts/gate_ci_guardrails_ops_"):',
        "            continue",
        "        if script_path in rows and rows[script_path] != desc:",
        '            die(f"duplicate TSV entry with conflicting description: {script_path}")',
        "        rows[script_path] = desc",
        "    return rows",
        "",
        'prove_text = prove_path.read_text(encoding="utf-8")',
        'index_text = index_path.read_text(encoding="utf-8")',
        'tsv_text = tsv_path.read_text(encoding="utf-8")',
        "",
        "cluster_rows = parse_cluster(prove_text)",
        "index_rows = parse_index(index_text)",
        "tsv_rows = parse_tsv(tsv_text)",
        "",
        "errors = []",
        "",
        "for script_path in sorted(set(tsv_rows) - set(index_rows)):",
        '    errors.append(f"TSV entry missing from Ops index: {script_path}")',
        "",
        "for script_path in sorted(set(index_rows) - set(tsv_rows)):",
        '    errors.append(f"Ops index entry missing from TSV registry: {script_path}")',
        "",
        "for script_path in sorted(set(tsv_rows) & set(index_rows)):",
        "    if tsv_rows[script_path] != index_rows[script_path]:",
        "        errors.append(",
        '            "description mismatch for "',
        "            + script_path",
        '            + " | TSV=\'"',
        "            + tsv_rows[script_path]",
        '            + "\' | INDEX=\'"',
        "            + index_rows[script_path]",
        '            + "\'"',
        "        )",
        "",
        "for script_path in sorted(tsv_rows):",
        "    if not (repo / script_path).is_file():",
        '        errors.append(f"TSV script path missing on disk: {script_path}")',
        "",
        "for script_path in sorted(set(cluster_rows) - set(tsv_rows)):",
        '    errors.append(f"Ops cluster script missing from TSV registry: {script_path}")',
        "",
        "for script_path in sorted(set(cluster_rows) - set(index_rows)):",
        '    errors.append(f"Ops cluster script missing from Ops index: {script_path}")',
        "",
        "if errors:",
        "    for err in errors:",
        "        print(err, file=sys.stderr)",
        "    raise SystemExit(1)",
        "",
        'print("OK: CI Guardrails ops label registry parity (v1)")',
        "LABEL_REGISTRY_PARITY_PY",
        "",
    ]
)

ADD_PATCHER_TEXT = "\n".join(
    [
        "from __future__ import annotations",
        "",
        "from pathlib import Path",
        "import runpy",
        "",
        "runpy.run_path(",
        '    str(Path(__file__).with_name("_patch_repair_ops_label_registry_parity_state_v7.py")),',
        '    run_name="__main__",',
        ")",
        "",
    ]
)

ADD_WRAPPER_TEXT = "\n".join(
    [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        'REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"',
        '"$REPO_ROOT/scripts/py" "$REPO_ROOT/scripts/_patch_add_gate_ci_guardrails_ops_label_registry_parity_v1.py"',
        "",
    ]
)

def write_text(path: Path, text: str, executable: bool = False) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current != text:
        path.write_text(text, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        desired = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        if mode != desired:
            os.chmod(path, desired)

def rewrite_cluster_block(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    start = None
    end = None
    for i, raw in enumerate(lines):
        line = raw.strip()
        if line == CLUSTER_LINES[0]:
            start = i
        if start is not None and line == CLUSTER_LINES[-1]:
            end = i
            break
    if start is not None and end is not None:
        new_lines = lines[:start] + CLUSTER_LINES + lines[end + 1 :]
        new_text = "\n".join(new_lines)
        if text.endswith("\n"):
            new_text += "\n"
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
        return
    old_block = OLD_CLUSTER_BLOCK
    new_block = NEW_CLUSTER_BLOCK
    if old_block in text:
        text = text.replace(old_block, new_block, 1)
        path.write_text(text, encoding="utf-8")
        return
    raise SystemExit(f"could not locate cluster block in {path}")

def patch_tsv() -> None:
    text = TSV.read_text(encoding="utf-8")
    lines = text.splitlines()
    kept = []
    inserted = False
    for raw in lines:
        if raw.startswith(TARGET + "\t"):
            continue
        if raw.startswith("scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh\t") and not inserted:
            kept.append(TARGET_TSV)
            inserted = True
        kept.append(raw)
    if not inserted:
        raise SystemExit(f"insertion anchor missing in {TSV}")
    new_text = "\n".join(kept)
    if text.endswith("\n"):
        new_text += "\n"
    if new_text != text:
        TSV.write_text(new_text, encoding="utf-8")

def patch_index() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if INDEX_BEGIN not in text or INDEX_END not in text:
        raise SystemExit(f"bounded section missing in {INDEX}")
    prefix, rest = text.split(INDEX_BEGIN, 1)
    body, suffix = rest.split(INDEX_END, 1)
    lines = body.strip("\n").splitlines()
    normalized = []
    inserted = False
    anchor = "- scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh — Ops guardrails label source exactness gate (v1)"
    target_line = "- " + TARGET + " — " + TARGET_DESC
    for raw in lines:
        line = raw.rstrip()
        if TARGET in line:
            continue
        line = line.replace("`scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh`", "scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh")
        if line == anchor and not inserted:
            normalized.append(target_line)
            inserted = True
        normalized.append(line)
    if not inserted:
        raise SystemExit(f"insertion anchor missing in bounded section of {INDEX}")
    new_text = prefix + INDEX_BEGIN + "\n" + "\n".join(normalized) + "\n" + INDEX_END + suffix
    if new_text != text:
        INDEX.write_text(new_text, encoding="utf-8")

def main() -> None:
    write_text(GATE, GATE_TEXT, executable=True)
    write_text(ADD_PATCHER, ADD_PATCHER_TEXT)
    write_text(ADD_WRAPPER, ADD_WRAPPER_TEXT, executable=True)
    rewrite_cluster_block(PROVE)
    rewrite_cluster_block(CLUSTER)
    patch_tsv()
    patch_index()

if __name__ == "__main__":
    main()
