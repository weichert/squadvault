from __future__ import annotations

from pathlib import Path
import stat

REPO = Path(__file__).resolve().parents[1]
PROVE_CI = REPO / "scripts" / "prove_ci.sh"
GATE = REPO / "scripts" / "gate_ci_guardrails_ops_renderer_shape_v1.sh"

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

tmp="$(mktemp)"
cleanup() {
  rm -f "$tmp"
}
trap cleanup EXIT

./scripts/py scripts/_render_ci_guardrails_ops_entrypoints_block_v1.py > "$tmp"

BEGIN_MARKER='<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->'
END_MARKER='<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->'

begin_count="$(grep -Fxc "$BEGIN_MARKER" "$tmp" || true)"
end_count="$(grep -Fxc "$END_MARKER" "$tmp" || true)"

if [ "$begin_count" -ne 1 ]; then
  echo "ERROR: renderer must emit exactly one begin marker; found $begin_count"
  exit 1
fi

if [ "$end_count" -ne 1 ]; then
  echo "ERROR: renderer must emit exactly one end marker; found $end_count"
  exit 1
fi

python3 - "$tmp" <<'PY_CHECK'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

b = text.find(begin)
e = text.find(end)

if b < 0:
    raise SystemExit("ERROR: begin marker missing")
if e < 0:
    raise SystemExit("ERROR: end marker missing")
if b >= e:
    raise SystemExit("ERROR: begin marker must occur before end marker")

if text.find(begin, b + len(begin)) != -1:
    raise SystemExit("ERROR: duplicate begin marker detected")
if text.find(end, e + len(end)) != -1:
    raise SystemExit("ERROR: duplicate end marker detected")

prefix = text[:b]
suffix = text[e + len(end):]
if prefix.strip():
    raise SystemExit("ERROR: renderer emitted non-whitespace content before bounded block")
if suffix.strip():
    raise SystemExit("ERROR: renderer emitted non-whitespace content after bounded block")

inner = text[b + len(begin):e]
nonempty = [line for line in inner.splitlines() if line.strip()]
if len(nonempty) < 2:
    raise SystemExit("ERROR: renderer emitted empty or too-small bounded body")

has_heading = any(
    line.lstrip().startswith("# ")
    or line.lstrip().startswith("## ")
    or line.lstrip().startswith("### ")
    for line in nonempty
)
has_list = any(line.lstrip().startswith("- ") for line in nonempty)
has_table = any("|" in line for line in nonempty)

if not (has_heading or has_list or has_table):
    raise SystemExit("ERROR: renderer body missing expected markdown structure")

print("OK: renderer shape contract satisfied")
PY_CHECK
"""

GATE_LINE = "bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh\n"

def write_if_changed(path: Path, text: str) -> bool:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True

def ensure_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def patch_prove_ci(text: str) -> str:
    if GATE_LINE in text:
        return text

    exactness = "bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh\n"
    parity = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"

    if exactness in text:
        return text.replace(exactness, exactness + GATE_LINE, 1)

    if parity in text:
        return text.replace(parity, GATE_LINE + parity, 1)

    raise SystemExit(
        "ERROR: could not find insertion anchor in scripts/prove_ci.sh "
        "(expected exactness or parity gate line)"
    )

def main() -> int:
    changed = False

    if write_if_changed(GATE, GATE_TEXT):
        ensure_executable(GATE)
        changed = True
    else:
        ensure_executable(GATE)

    prove_ci_text = PROVE_CI.read_text(encoding="utf-8")
    new_prove_ci_text = patch_prove_ci(prove_ci_text)
    if new_prove_ci_text != prove_ci_text:
        PROVE_CI.write_text(new_prove_ci_text, encoding="utf-8")
        changed = True

    if changed:
        print("OK: added CI Guardrails Ops renderer shape gate (v1)")
    else:
        print("OK: CI Guardrails Ops renderer shape gate already present (noop)")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
