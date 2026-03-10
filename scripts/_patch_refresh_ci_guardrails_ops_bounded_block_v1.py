from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
RENDER = REPO / "scripts/_render_ci_guardrails_ops_entrypoints_block_v1.py"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"


def fail(msg: str) -> "None":
    raise SystemExit(msg)


def main() -> int:
    text = DOC.read_text(encoding="utf-8")

    begin_count = text.count(BEGIN)
    end_count = text.count(END)
    if begin_count < 1:
        fail(f"expected at least one begin anchor: {BEGIN!r}")
    if end_count < 1:
        fail(f"expected at least one end anchor: {END!r}")

    proc = subprocess.run(
        [str(REPO / "scripts/py"), str(RENDER)],
        cwd=REPO,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        fail("renderer failed")

    rendered = proc.stdout.rstrip("\n")
    if not rendered.strip():
        fail("renderer produced empty output")
    if rendered.count(BEGIN) != 1 or rendered.count(END) != 1:
        fail("renderer output must contain exactly one begin marker and one end marker")

    start = text.index(BEGIN)
    end = text.rindex(END) + len(END)
    if end <= start:
        fail("malformed bounded region")

    old_block = text[start:end]
    new_block = rendered

    if old_block == new_block:
        return 0

    updated = text[:start] + new_block + text[end:]
    DOC.write_text(updated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
