from __future__ import annotations

from pathlib import Path
import os
import stat

REPO = Path(__file__).resolve().parents[1]

GATE = REPO / "scripts" / "gate_ci_guardrails_ops_label_registry_parity_v1.sh"
PROVE = REPO / "scripts" / "prove_ci.sh"
INDEX = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
CLUSTER = REPO / "scripts" / "gate_ci_guardrails_ops_cluster_canonical_v1.sh"

TARGET_SCRIPT = "scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh"
TARGET_DESC = "Ensures TSV registry ↔ Ops index ↔ gate scripts stay perfectly synchronized."
TARGET_BULLET = f"- `{TARGET_SCRIPT}` — {TARGET_DESC}"
TARGET_TSV_LINE = f"{TARGET_SCRIPT}\t{TARGET_DESC}"

INDEX_BEGIN = "SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN"
INDEX_END = "SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END"

PROVE_INSERT_BEFORE = "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh"
INDEX_INSERT_BEFORE = "scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh"
TSV_INSERT_BEFORE = "scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh"

GATE_TEXT = "\n".join(
    [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        'REPO_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"',
        "",
        'cd "$REPO_ROOT"',
        "",
        '"$REPO_ROOT/scripts/py" - <<'"'"'GATE_PY'"'"'',
        "from __future__ import annotations",
        "",
        "from pathlib import Path",
        "import re",
        "import sys",
        "",
        "repo = Path.cwd()",
        'tsv_path = repo / "docs/80_indices/ops/CI_Guardrail_Entrypoint_Labels_v1.tsv"',
        'index_path = repo / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"',
        "",
        'index_begin = "SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN"',
        'index_end = "SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END"',
        "",
        "def die(msg: str) -> None:",
        "    print(msg, file=sys.stderr)",
        "    raise SystemExit(1)",
        "",
        "if not tsv_path.is_file():",
        '    die(f"missing file: {tsv_path}")',
        "",
        "if not index_path.is_file():",
        '    die(f"missing file: {index_path}")',
        "",
        "tsv_rows = {}",
        'for raw in tsv_path.read_text(encoding="utf-8").splitlines():',
        "    line = raw.strip()",
        "    if not line:",
        "        continue",
        '    if line.startswith("#"):',
        "        continue",
        '    cols = raw.split("\\t")',
        "    if len(cols) < 2:",
        "        continue",
        "    script_path = cols[0].strip()",
        "    desc = cols[-1].strip()",
        '    if not script_path.startswith("scripts/gate_"):',
        "        continue",
        '    if not script_path.endswith(".sh"):',
        "        continue",
        "    if script_path in tsv_rows and tsv_rows[script_path] != desc:",
        '        die(f"duplicate TSV entry with conflicting description: {script_path}")',
        "    tsv_rows[script_path] = desc",
        "",
        'index_text = index_path.read_text(encoding="utf-8")',
        "if index_begin not in index_text or index_end not in index_text:",
        '    die("missing CI guardrails entrypoints bounded section in Ops index")',
        "",
        "prefix, rest = index_text.split(index_begin, 1)",
        "body, suffix = rest.split(index_end, 1)",
        "index_body = body.strip(\"\\n\")",
        "",
        "index_rows = {}",
        "for raw in index_body.splitlines():",
        "    line = raw.strip()",
        '    if not line.startswith("- "):',
        "        continue",
        '    found = re.match(r"^-\\s+`?(scripts/gate_[^`\\s]+\\.sh)`?\\s*(?:—|-|:)\\s*(.+?)\\s*$", line)',
        "    if not found:",
        "        continue",
        "    script_path = found.group(1).strip()",
        "    desc = found.group(2).strip()",
        "    if script_path in index_rows and index_rows[script_path] != desc:",
        '        die(f"duplicate Ops index entry with conflicting description: {script_path}")',
        "    index_rows[script_path] = desc",
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
        "if errors:",
        "    for err in errors:",
        "        print(err, file=sys.stderr)",
        "    raise SystemExit(1)",
        "",
        'print("OK: CI Guardrails ops label registry parity (v1)")',
        "GATE_PY",
        "",
    ]
)

OLD_CLUSTER_BLOCK = "\n".join(
    [
        "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
        "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
    ]
)

NEW_CLUSTER_BLOCK = "\n".join(
    [
        "bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
        "bash scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh",
        "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
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

def patch_prove_ci() -> None:
    text = PROVE.read_text(encoding="utf-8")
    target = "bash scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh"
    if target in text:
        lines = text.splitlines()
        kept = []
        seen = False
        for line in lines:
            if line == target:
                if seen:
                    continue
                seen = True
            kept.append(line)
        text = "\n".join(kept) + ("\n" if text.endswith("\n") else "")
        current_index = text.find(target)
        anchor_index = text.find(PROVE_INSERT_BEFORE)
        if current_index == -1 or anchor_index == -1 or current_index > anchor_index:
            text = text.replace(target + "\n", "", 1)
            anchor = PROVE_INSERT_BEFORE + "\n"
            if anchor not in text:
                raise SystemExit(f"anchor missing in {PROVE}")
            text = text.replace(anchor, target + "\n" + anchor, 1)
        PROVE.write_text(text, encoding="utf-8")
        return

    anchor = PROVE_INSERT_BEFORE + "\n"
    if anchor not in text:
        raise SystemExit(f"anchor missing in {PROVE}")
    text = text.replace(anchor, target + "\n" + anchor, 1)
    PROVE.write_text(text, encoding="utf-8")

def patch_index() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if INDEX_BEGIN not in text or INDEX_END not in text:
        raise SystemExit(f"bounded section missing in {INDEX}")

    prefix, rest = text.split(INDEX_BEGIN, 1)
    body, suffix = rest.split(INDEX_END, 1)
    lines = body.strip("\n").splitlines()

    lines = [line for line in lines if TARGET_SCRIPT not in line]

    inserted = False
    for i, line in enumerate(lines):
        if INDEX_INSERT_BEFORE in line:
            lines.insert(i, TARGET_BULLET)
            inserted = True
            break
    if not inserted:
        raise SystemExit(f"insertion anchor missing in bounded section of {INDEX}")

    new_body = "\n".join(lines)
    new_text = prefix + INDEX_BEGIN + "\n" + new_body + "\n" + INDEX_END + suffix
    if new_text != text:
        INDEX.write_text(new_text, encoding="utf-8")

def patch_tsv() -> None:
    text = TSV.read_text(encoding="utf-8")
    lines = text.splitlines()

    lines = [line for line in lines if not line.startswith(TARGET_SCRIPT + "\t")]

    inserted = False
    for i, line in enumerate(lines):
        if line.startswith(TSV_INSERT_BEFORE + "\t"):
            lines.insert(i, TARGET_TSV_LINE)
            inserted = True
            break
    if not inserted:
        raise SystemExit(f"insertion anchor missing in {TSV}")

    new_text = "\n".join(lines)
    if text.endswith("\n"):
        new_text += "\n"
    if new_text != text:
        TSV.write_text(new_text, encoding="utf-8")

def patch_cluster_canonical_gate() -> None:
    text = CLUSTER.read_text(encoding="utf-8")
    if NEW_CLUSTER_BLOCK in text:
        return
    if OLD_CLUSTER_BLOCK not in text:
        raise SystemExit(f"expected canonical cluster block not found in {CLUSTER}")
    text = text.replace(OLD_CLUSTER_BLOCK, NEW_CLUSTER_BLOCK, 1)
    CLUSTER.write_text(text, encoding="utf-8")

def main() -> None:
    write_text(GATE, GATE_TEXT, executable=True)
    patch_prove_ci()
    patch_index()
    patch_tsv()
    patch_cluster_canonical_gate()

if __name__ == "__main__":
    main()
