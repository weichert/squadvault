from __future__ import annotations

from pathlib import Path
import re

PROVE = Path("scripts/prove_ci.sh")

ANCHOR_BEGIN = "# === SV_ANCHOR: docs_gates (v1) ==="
ANCHOR_END = "# === /SV_ANCHOR: docs_gates (v1) ==="

# Canonical block we want directly under the anchor (ECHO SAFE).
GATE_BLOCK = """\
echo "==> Gate: CI Guardrails ops entrypoints section + TOC (v2)"
bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh

"""

# Detect and remove any existing (possibly broken) gate blocks we previously injected.
# This matches:
#  - bare banner:    ==> Gate: ...
#  - echoed banner:  echo "==> Gate: ..."
#  - optional presence/absence of the banner line
#  - required bash invocation line
RE_BLOCK = re.compile(
    r"(?ms)^"
    r"(?:(?:echo )?\"?==> Gate: CI Guardrails ops entrypoints section \+ TOC \(v2\)\"?\n)?"
    r"bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2\.sh\n"
    r"(?:\n)?"
)

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text, encoding="utf-8")

def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")

def main() -> None:
    if not PROVE.exists():
        _refuse(f"missing required file: {PROVE}")

    s = _read(PROVE)

    if ANCHOR_BEGIN not in s or ANCHOR_END not in s:
        _refuse("missing docs_gates anchor markers in scripts/prove_ci.sh (expected v1 anchor)")

    a0 = s.find(ANCHOR_BEGIN)
    a1 = s.find(ANCHOR_END, a0)
    if a1 == -1:
        _refuse(f"found anchor begin but missing anchor end: {ANCHOR_END}")

    a1_end = a1 + len(ANCHOR_END)
    if a1_end < len(s) and s[a1_end:a1_end+1] == "\n":
        a1_end += 1

    matches = list(RE_BLOCK.finditer(s))
    if len(matches) > 1:
        _refuse(f"multiple ops entrypoints gate blocks found in {PROVE}; refuse to guess which to keep")

    if len(matches) == 1:
        m = matches[0]
        s = s[:m.start()] + s[m.end():]

    # If the canonical (echo-safe) block is already directly under anchor, done.
    if s[a1_end:].startswith(GATE_BLOCK):
        _write(PROVE, s)
        return

    out = s[:a1_end] + GATE_BLOCK + s[a1_end:]
    _write(PROVE, out)

if __name__ == "__main__":
    main()
