#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"
DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
RENDER = REPO_ROOT / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"
GATE = REPO_ROOT / "scripts" / "gate_ci_guardrails_ops_entrypoint_exactness_v1.sh"

BLOCK_BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
BLOCK_END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

PARITY_LINE = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh"
EXACTNESS_LINE = "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh"
SECTION_LINE = "bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_if_changed(path: Path, content: str) -> bool:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True

def canonicalize_prove_ci(text: str) -> str:
    if text.count(PARITY_LINE) != 1:
        raise RuntimeError(
            f"expected exactly one parity gate anchor in {PROVE.relative_to(REPO_ROOT)}"
        )
    if text.count(SECTION_LINE) != 1:
        raise RuntimeError(
            f"expected exactly one section gate anchor in {PROVE.relative_to(REPO_ROOT)}"
        )

    had_trailing_newline = text.endswith("\n")
    lines = text.splitlines()

    filtered: list[str] = []
    for line in lines:
        if line == EXACTNESS_LINE:
            continue
        filtered.append(line)

    out: list[str] = []
    inserted = False
    for line in filtered:
        out.append(line)
        if line == PARITY_LINE:
            out.append(EXACTNESS_LINE)
            inserted = True

    if not inserted:
        raise RuntimeError("failed to insert exactness gate after parity gate")

    if out.count(EXACTNESS_LINE) != 1:
        raise RuntimeError("exactness gate insertion did not converge to exactly one line")

    if out.index(EXACTNESS_LINE) > out.index(SECTION_LINE):
        raise RuntimeError("exactness gate must appear before section gate")

    result = "\n".join(out)
    if had_trailing_newline:
        result += "\n"
    return result

def replace_bounded_block(text: str, new_block: str) -> str:
    if text.count(BLOCK_BEGIN) != 1:
        raise RuntimeError(
            f"expected exactly one begin marker in {DOC.relative_to(REPO_ROOT)}"
        )
    if text.count(BLOCK_END) != 1:
        raise RuntimeError(
            f"expected exactly one end marker in {DOC.relative_to(REPO_ROOT)}"
        )

    start = text.index(BLOCK_BEGIN)
    end = text.index(BLOCK_END)
    if end < start:
        raise RuntimeError("bounded block markers are out of order")

    end_line = text.find("\n", end)
    if end_line == -1:
        end_line = len(text)
    else:
        end_line += 1

    return text[:start] + new_block + text[end_line:]

def render_block_from_prove_text(prove_text: str) -> str:
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".sh",
        ) as tmp:
            tmp.write(prove_text)
            tmp_path = Path(tmp.name)

        rendered = subprocess.check_output(
            [sys.executable, "-B", str(RENDER), "--prove", str(tmp_path)],
            cwd=str(REPO_ROOT),
            text=True,
        )
        if BLOCK_BEGIN not in rendered or BLOCK_END not in rendered:
            raise RuntimeError("renderer output is missing required bounded block markers")
        return rendered
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()

def ensure_required_files() -> None:
    for path in (PROVE, DOC, RENDER, GATE):
        if not path.is_file():
            raise RuntimeError(f"missing required file: {path.relative_to(REPO_ROOT)}")

def main() -> int:
    ensure_required_files()

    prove_before = read_text(PROVE)
    prove_after = canonicalize_prove_ci(prove_before)

    rendered_block = render_block_from_prove_text(prove_after)

    doc_before = read_text(DOC)
    doc_after = replace_bounded_block(doc_before, rendered_block)

    doc_changed = write_if_changed(DOC, doc_after)
    prove_changed = write_if_changed(PROVE, prove_after)

    if doc_changed:
        print(f"OK: updated {DOC.relative_to(REPO_ROOT)}")
    else:
        print(f"OK: {DOC.relative_to(REPO_ROOT)} already canonical")

    if prove_changed:
        print(f"OK: updated {PROVE.relative_to(REPO_ROOT)}")
    else:
        print(f"OK: {PROVE.relative_to(REPO_ROOT)} already canonical")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
