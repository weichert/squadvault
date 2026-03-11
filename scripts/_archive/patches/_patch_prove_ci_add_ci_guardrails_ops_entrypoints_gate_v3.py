from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")
GATE = Path("scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh")

INSERT_BLOCK = """\
==> Gate: CI Guardrails ops entrypoints section + TOC (v2)
bash scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh

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
    if not GATE.exists():
        _refuse(f"missing required file: {GATE}")

    s = _read(PROVE)

    # Idempotent: if already wired, do nothing.
    if "gate_ci_guardrails_ops_entrypoints_section_v2.sh" in s:
        return

    # Find a stable insertion point: the docs integrity gate banner line (version may vary)
    lines = s.splitlines(keepends=True)
    idx = None
    for i, line in enumerate(lines):
        if "Docs integrity gate" in line and line.lstrip().startswith("==>"):
            idx = i
            break

    if idx is None:
        _refuse("could not find insertion anchor containing 'Docs integrity gate' banner line in scripts/prove_ci.sh")

    out_lines = lines[:idx] + [INSERT_BLOCK] + lines[idx:]
    _write(PROVE, "".join(out_lines))


if __name__ == "__main__":
    main()
