from __future__ import annotations

from pathlib import Path

V1_GATE = Path("scripts/gate_docs_mutation_guardrail_v1.sh")
CI_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

DEPRECATION_SNIPPET = """\
# NOTE (v1 deprecation):
#   This gate is superseded by:
#     scripts/gate_docs_mutation_guardrail_v2.sh
#   Kept for historical reference only. prove_ci wires v2.
#
"""

INDEX_MARKER = "<!-- SV_DOCS_MUTATION_GUARDRAIL_GATE: v2 (v1) -->"
INDEX_BULLET = "- scripts/gate_docs_mutation_guardrail_v2.sh — Docs Mutation Guardrail Gate (canonical)"

INDEX_BLOCK = f"""\

{INDEX_MARKER}
{INDEX_BULLET}
"""

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def _ensure_v1_gate_has_deprecation(text: str) -> str:
    if "This gate is superseded by" in text and "gate_docs_mutation_guardrail_v2.sh" in text:
        return text

    lines = text.splitlines(True)
    out: list[str] = []
    inserted = False

    # Insert right after shebang (and any immediate blank line)
    i = 0
    if i < len(lines) and lines[i].startswith("#!"):
        out.append(lines[i])
        i += 1
        # preserve one optional blank line
        if i < len(lines) and lines[i].strip() == "":
            out.append(lines[i])
            i += 1
        out.append(DEPRECATION_SNIPPET)
        inserted = True

    # Append remainder
    out.extend(lines[i:])

    if not inserted:
        # Fallback: prepend if no shebang found (shouldn't happen)
        return DEPRECATION_SNIPPET + text

    return "".join(out)

def _dedupe_and_append_index_block(text: str) -> str:
    # Remove any prior occurrences of the marker or bullet, then append once.
    lines = text.splitlines(True)
    out: list[str] = []
    for ln in lines:
        if INDEX_MARKER in ln:
            continue
        if INDEX_BULLET in ln:
            continue
        out.append(ln)

    new_text = "".join(out)
    if not new_text.endswith("\n"):
        new_text += "\n"
    new_text += INDEX_BLOCK
    return new_text

def main() -> None:
    if not V1_GATE.exists():
        raise SystemExit(f"missing canonical file: {V1_GATE}")
    if not CI_INDEX.exists():
        raise SystemExit(f"missing canonical file: {CI_INDEX}")

    # 1) Deprecate v1 gate
    v1_text = _read(V1_GATE)
    v1_new = _ensure_v1_gate_has_deprecation(v1_text)
    if v1_new != v1_text:
        _write(V1_GATE, v1_new)

    # 2) Add v2 gate discoverability to CI index (deduped)
    idx_text = _read(CI_INDEX)
    idx_new = _dedupe_and_append_index_block(idx_text)
    if idx_new != idx_text:
        _write(CI_INDEX, idx_new)

if __name__ == "__main__":
    main()
