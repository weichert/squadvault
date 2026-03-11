from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

# Insert just before the pytest unit tests banner (stable, highly visible).
NEEDLE = "==> unit tests (pytest; tracked Tests/ paths; bash3-safe)\n"

INSERT = """\
==> Gate: CI Guardrails ops entrypoints section (v1)
bash scripts/gate_ci_guardrails_ops_entrypoints_section_v1.sh

"""

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

    if "gate_ci_guardrails_ops_entrypoints_section_v1.sh" in s:
        return

    if NEEDLE not in s:
        _refuse("could not find insertion anchor: pytest unit tests banner")

    out = s.replace(NEEDLE, INSERT + NEEDLE, 1)
    _write(PROVE, out)

if __name__ == "__main__":
    main()
