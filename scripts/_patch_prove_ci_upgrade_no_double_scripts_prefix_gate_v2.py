from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

OLD = """echo "==> Gate: no double scripts prefix (v1)"
bash scripts/gate_no_double_scripts_prefix_v1.sh

"""

NEW = """echo "==> Gate: no double scripts prefix (v2)"
bash scripts/gate_no_double_scripts_prefix_v2.sh

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

    if "gate_no_double_scripts_prefix_v2.sh" in s:
        return

    if OLD not in s:
        _refuse("could not find the exact v1 no-double-scripts gate block to replace")

    out = s.replace(OLD, NEW, 1)
    _write(PROVE, out)

if __name__ == "__main__":
    main()
