from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROVE = ROOT / "scripts" / "prove_ci.sh"
GATE = ROOT / "scripts" / "gate_ci_guardrails_execution_order_lock_v1.sh"
TSV = ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrail_Entrypoint_Labels_v1.tsv"
INDEX = ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"
RENDER = ROOT / "scripts" / "_render_ci_guardrails_ops_entrypoints_block_v1.py"

NEW_PATH = "scripts/gate_ci_guardrails_execution_order_lock_v1.sh"
NEW_LABEL = "CI Guardrails execution order lock (v1)"

def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)

# ------------------------------------------------------------
# [1] prove_ci.sh: sort only gate invocation lines
# ------------------------------------------------------------
prove_text = PROVE.read_text(encoding="utf-8")
prove_lines = prove_text.splitlines()

gate_line_re = re.compile(r"^bash scripts/gate_[A-Za-z0-9_]+\.sh(?: .*)?$")
all_gate_lines = [line for line in prove_lines if gate_line_re.match(line)]
if not all_gate_lines:
    fail("no gate invocation lines found in scripts/prove_ci.sh")

sorted_gate_lines = sorted(all_gate_lines)

if all_gate_lines != sorted_gate_lines:
    it = iter(sorted_gate_lines)
    new_lines = []
    for line in prove_lines:
        if gate_line_re.match(line):
            new_lines.append(next(it))
        else:
            new_lines.append(line)
    PROVE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("OK: sorted gate invocation lines in scripts/prove_ci.sh")
else:
    print("OK: scripts/prove_ci.sh gate invocation lines already sorted")

prove_text = PROVE.read_text(encoding="utf-8")

# ------------------------------------------------------------
# [2] sync EXPECTED block to canonical sorted CI guardrail subset
# ------------------------------------------------------------
ci_guardrail_re = re.compile(r"^bash scripts/gate_ci_guardrails_[A-Za-z0-9_]+\.sh$", re.M)
expected_lines = ci_guardrail_re.findall(prove_text)
if not expected_lines:
    fail("no CI guardrail gate lines found in scripts/prove_ci.sh")

gate_text = GATE.read_text(encoding="utf-8")
expected_block_re = re.compile(
    r"EXPECTED = \[\n(?:    \".*\",\n)+\]",
    re.M,
)

replacement = "EXPECTED = [\n" + "".join(f'    "{line}",\n' for line in expected_lines) + "]"

gate_updated, count = expected_block_re.subn(replacement, gate_text, count=1)
if count != 1:
    fail("could not locate EXPECTED block in gate_ci_guardrails_execution_order_lock_v1.sh")

if gate_updated != gate_text:
    GATE.write_text(gate_updated, encoding="utf-8")
    print("OK: synced execution-order EXPECTED block to canonical sorted CI guardrail order")
else:
    print("OK: execution-order EXPECTED block already canonical")

# ------------------------------------------------------------
# [3] TSV label registry: ensure missing row exists, then sort CI rows
# ------------------------------------------------------------
tsv_text = TSV.read_text(encoding="utf-8")
tsv_lines = tsv_text.splitlines()

nonempty = [line for line in tsv_lines if line.strip()]
header = nonempty[0] if nonempty and "\t" in nonempty[0] and nonempty[0].lower().startswith("path\t") else None

body_lines = tsv_lines[:]
if header is not None:
    body_lines = tsv_lines[1:]

rows = [line for line in body_lines if line.strip()]
if not any(line.split("\t")[0] == NEW_PATH for line in rows):
    template_idx = None
    for i, line in enumerate(rows):
        if line.startswith("scripts/gate_ci_guardrails_surface_freeze_v1.sh\t"):
            template_idx = i
            break
    if template_idx is None:
        for i, line in enumerate(rows):
            if line.startswith("scripts/gate_ci_guardrails_registry_completeness_v1.sh\t"):
                template_idx = i
                break
    if template_idx is None:
        fail("could not find template CI guardrail TSV row")

    parts = rows[template_idx].split("\t")
    if len(parts) < 2:
        fail("template TSV row has unexpected shape")

    parts[0] = NEW_PATH
    parts[1] = NEW_LABEL
    rows.append("\t".join(parts))
    print("OK: added execution order lock row to CI_Guardrail_Entrypoint_Labels_v1.tsv")
else:
    print("OK: TSV label registry already contains execution order lock entry")

ci_rows = []
other_rows = []
for line in rows:
    if line.startswith("scripts/gate_ci_guardrails_"):
        ci_rows.append(line)
    else:
        other_rows.append(line)

ci_rows_sorted = sorted(ci_rows, key=lambda s: s.split("\t", 1)[0])
new_rows = other_rows + ci_rows_sorted

new_tsv_lines = ([header] if header is not None else []) + new_rows
new_tsv_text = "\n".join(new_tsv_lines) + "\n"
if new_tsv_text != tsv_text:
    TSV.write_text(new_tsv_text, encoding="utf-8")
    print("OK: normalized CI guardrail TSV row ordering")
else:
    print("OK: CI guardrail TSV row ordering already canonical")

# ------------------------------------------------------------
# [4] Re-render bounded ops entrypoints block in ops index
# ------------------------------------------------------------
if not RENDER.exists():
    fail("missing renderer: scripts/_render_ci_guardrails_ops_entrypoints_block_v1.py")
if not INDEX.exists():
    fail(f"missing ops index: {INDEX}")

rendered = subprocess.check_output(
    [str(ROOT / "scripts" / "py"), str(RENDER)],
    cwd=str(ROOT),
    text=True,
)

index_text = INDEX.read_text(encoding="utf-8")
index_lines = index_text.splitlines()

begin_idx = None
end_idx = None

for i, line in enumerate(index_lines):
    u = line.upper()
    if "BEGIN" in u and "ENTRYPOINT" in u and "CI_GUARDRAIL" in u:
        begin_idx = i
        break
if begin_idx is None:
    for i, line in enumerate(index_lines):
        u = line.upper()
        if "BEGIN" in u and "ENTRYPOINT" in u and "GUARDRAIL" in u:
            begin_idx = i
            break
if begin_idx is None:
    fail("could not find CI guardrail ops entrypoints BEGIN marker in ops index")

for i in range(begin_idx + 1, len(index_lines)):
    u = index_lines[i].upper()
    if "END" in u and "ENTRYPOINT" in u and ("CI_GUARDRAIL" in u or "GUARDRAIL" in u):
        end_idx = i
        break
if end_idx is None or end_idx <= begin_idx:
    fail("could not find CI guardrail ops entrypoints END marker in ops index")

new_index_lines = (
    index_lines[: begin_idx + 1]
    + rendered.rstrip("\n").splitlines()
    + index_lines[end_idx:]
)
new_index_text = "\n".join(new_index_lines) + "\n"

if new_index_text != index_text:
    INDEX.write_text(new_index_text, encoding="utf-8")
    print("OK: re-rendered CI guardrail ops entrypoints block in CI_Guardrails_Index_v1.0.md")
else:
    print("OK: CI guardrail ops entrypoints block already canonical")

print("OK: Phase 7.12 repair patch applied")
