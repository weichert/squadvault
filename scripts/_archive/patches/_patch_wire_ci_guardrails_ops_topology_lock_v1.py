from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PROVE = REPO / "scripts" / "prove_ci.sh"
INDEX = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
TSV = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
CLUSTER = REPO / "scripts" / "gate_ci_guardrails_ops_cluster_canonical_v1.sh"

INDEX_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
INDEX_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

ORDER_LOCK = "scripts/gate_ci_guardrails_ops_entrypoint_order_lock_v1.sh"
LABEL_PARITY = "scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh"
LABEL_SOURCE = "scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh"
TOPOLOGY = "scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh"
ALLOWLIST = "scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh"

INSERT_PATHS = [ORDER_LOCK, LABEL_PARITY, LABEL_SOURCE, TOPOLOGY]

LABELS = {
    ORDER_LOCK: "Ops guardrails entrypoint order lock gate (v1)",
    LABEL_PARITY: "Ensures TSV registry ↔ Ops index ↔ gate scripts stay perfectly synchronized.",
    LABEL_SOURCE: "Ops guardrails label source exactness gate (v1)",
    TOPOLOGY: "Ops guardrails topology uniqueness gate (v1)",
}

OPS_CLUSTER = [
    "scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh",
    ORDER_LOCK,
    "scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh",
    "scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh",
    LABEL_PARITY,
    LABEL_SOURCE,
    "scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh",
    TOPOLOGY,
]


def write_if_changed(path: Path, new_text: str) -> None:
    old = path.read_text(encoding="utf-8")
    if old != new_text:
        path.write_text(new_text, encoding="utf-8")


def patch_prove() -> None:
    lines = PROVE.read_text(encoding="utf-8").splitlines()
    pos = [i for i, line in enumerate(lines) if line.strip().startswith("bash scripts/gate_ci_guardrails_ops_")]
    if not pos:
        raise SystemExit("ERROR: no Ops cluster found in scripts/prove_ci.sh")
    start = min(pos)
    end = max(pos) + 1
    repl = [f"bash {p}" for p in OPS_CLUSTER]
    write_if_changed(PROVE, "\n".join(lines[:start] + repl + lines[end:]) + "\n")


def patch_cluster() -> None:
    text = CLUSTER.read_text(encoding="utf-8")
    marker = "expected_lines = ["
    start = text.find(marker)
    if start == -1:
        raise SystemExit("ERROR: expected_lines block not found")
    list_start = start + len(marker)
    end = text.find("\n]", list_start)
    if end == -1:
        raise SystemExit("ERROR: closing bracket for expected_lines not found")
    rendered = "\n".join(f'    "bash {p}",' for p in OPS_CLUSTER)
    new_text = text[:list_start] + "\n" + rendered + text[end:]
    write_if_changed(CLUSTER, new_text)


def reorder_rows(lines: list[str]) -> list[str]:
    parsed = []
    for raw in lines:
        if not raw.strip():
            continue
        path, label = raw.split("\t", 1)
        parsed.append((path.strip(), label))

    kept = [(p, l) for p, l in parsed if p not in INSERT_PATHS]
    out = []
    inserted = False
    for p, l in kept:
        out.append((p, l))
        if p == ALLOWLIST:
            for ip in INSERT_PATHS:
                out.append((ip, LABELS[ip]))
            inserted = True
    if not inserted:
        raise SystemExit(f"ERROR: anchor not found in TSV: {ALLOWLIST}")
    return [f"{p}\t{l}" for p, l in out]


def patch_tsv() -> None:
    lines = TSV.read_text(encoding="utf-8").splitlines()
    new_lines = reorder_rows(lines)
    write_if_changed(TSV, "\n".join(new_lines) + "\n")


def patch_index() -> None:
    text = INDEX.read_text(encoding="utf-8")
    if INDEX_BEGIN not in text or INDEX_END not in text:
        raise SystemExit("ERROR: bounded index markers not found")
    before, rest = text.split(INDEX_BEGIN, 1)
    block, after = rest.split(INDEX_END, 1)

    raw_lines = block.splitlines()
    bullets = []
    seen_bullet = False
    prelude = []
    trailer = []

    for line in raw_lines:
        stripped = line.strip()
        if stripped.startswith("- scripts/") and " — " in stripped:
            seen_bullet = True
            path = stripped.split(" — ", 1)[0][2:].strip()
            label = stripped.split(" — ", 1)[1]
            bullets.append((path, label))
            continue
        if not seen_bullet:
            prelude.append(line)
        else:
            trailer.append(line)

    kept = [(p, l) for p, l in bullets if p not in INSERT_PATHS]
    out = []
    inserted = False
    for p, l in kept:
        out.append((p, l))
        if p == ALLOWLIST:
            for ip in INSERT_PATHS:
                out.append((ip, LABELS[ip]))
            inserted = True
    if not inserted:
        raise SystemExit(f"ERROR: anchor not found in index block: {ALLOWLIST}")

    # Normalize header region: no leading blank lines after BEGIN; exactly one blank
    # line between the marker and the section heading.
    while prelude and prelude[0].strip() == "":
        prelude.pop(0)
    while prelude and prelude[-1].strip() == "":
        prelude.pop()

    bullet_lines = [f"- {p} — {l}" for p, l in out]

    new_block_lines = []
    if prelude:
        new_block_lines.extend(prelude)
    new_block_lines.append("")
    new_block_lines.extend(bullet_lines)
    new_block_lines.extend(trailer)

    new_text = before + INDEX_BEGIN + "\n" + "\n".join(new_block_lines) + "\n" + INDEX_END + after
    write_if_changed(INDEX, new_text)


def main() -> int:
    patch_prove()
    patch_cluster()
    patch_tsv()
    patch_index()
    print("OK: wired CI Guardrails Ops topology lock surfaces (v1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
