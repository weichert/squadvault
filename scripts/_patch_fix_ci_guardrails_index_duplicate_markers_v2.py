from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
RENDER = ROOT / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"

BEGIN_MARK = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END_MARK = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)

if not INDEX.exists():
    fail(f"missing index: {INDEX}")
if not RENDER.exists():
    fail(f"missing renderer: {RENDER}")

text = INDEX.read_text(encoding="utf-8")
lines = text.splitlines()

begin_idxs = [i for i, line in enumerate(lines) if line.strip() == BEGIN_MARK]
end_idxs = [i for i, line in enumerate(lines) if line.strip() == END_MARK]

if not begin_idxs:
    fail("no CI guardrail BEGIN markers found")
if not end_idxs:
    fail("no CI guardrail END markers found")

first_begin = begin_idxs[0]
last_end = end_idxs[-1]

if last_end <= first_begin:
    fail("last END marker does not occur after first BEGIN marker")

rendered = subprocess.check_output(
    [str(ROOT / "scripts" / "py"), str(RENDER)],
    cwd=str(ROOT),
    text=True,
).rstrip("\n").splitlines()

if not rendered:
    fail("renderer returned empty output")

new_lines = lines[:first_begin] + rendered + lines[last_end + 1:]
new_text = "\n".join(new_lines) + "\n"
INDEX.write_text(new_text, encoding="utf-8")

final_lines = INDEX.read_text(encoding="utf-8").splitlines()
final_begin = [i for i, line in enumerate(final_lines) if line.strip() == BEGIN_MARK]
final_end = [i for i, line in enumerate(final_lines) if line.strip() == END_MARK]

if len(final_begin) != 1 or len(final_end) != 1:
    fail(
        f"expected exactly one CI guardrail marker pair after rewrite; "
        f"found begin={len(final_begin)} end={len(final_end)}"
    )

if final_end[0] <= final_begin[0]:
    fail("final END marker does not occur after final BEGIN marker")

print("OK: replaced duplicate CI guardrail bounded block with single canonical rendered block")
