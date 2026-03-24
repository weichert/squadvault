from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
RENDER = ROOT / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"

def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)

text = INDEX.read_text(encoding="utf-8")
lines = text.splitlines()

marker_idxs = []
for i, line in enumerate(lines):
    u = line.upper()
    if "ENTRYPOINT" in u and "GUARDRAIL" in u and ("BEGIN" in u or "END" in u):
        marker_idxs.append(i)

if len(marker_idxs) < 2:
    fail("expected at least one BEGIN/END marker pair for CI guardrail entrypoints block")
if len(marker_idxs) % 2 != 0:
    fail(f"expected an even number of CI guardrail marker lines, found {len(marker_idxs)}")

first_begin = marker_idxs[0]
last_end = marker_idxs[-1]

begin_line = lines[first_begin]
end_line = lines[last_end]

rendered = subprocess.check_output(
    [str(ROOT / "scripts" / "py"), str(RENDER)],
    cwd=str(ROOT),
    text=True,
).rstrip("\n").splitlines()

new_lines = (
    lines[:first_begin + 1]
    + rendered
    + lines[last_end:]
)

new_text = "\n".join(new_lines) + "\n"
INDEX.write_text(new_text, encoding="utf-8")

# verify exactly one begin + one end remain for this block family
final_lines = INDEX.read_text(encoding="utf-8").splitlines()
begin_count = 0
end_count = 0
for line in final_lines:
    u = line.upper()
    if "ENTRYPOINT" in u and "GUARDRAIL" in u and "BEGIN" in u:
        begin_count += 1
    if "ENTRYPOINT" in u and "GUARDRAIL" in u and "END" in u:
        end_count += 1

if begin_count != 1 or end_count != 1:
    fail(
        "duplicate CI guardrail entrypoint markers remain "
        f"(begin={begin_count}, end={end_count})"
    )

print("OK: collapsed duplicate CI guardrail entrypoint markers to one bounded block")
