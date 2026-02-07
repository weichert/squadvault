from __future__ import annotations

from pathlib import Path

GATE_V2 = Path("scripts/gate_no_double_scripts_prefix_v2.sh")

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text, encoding="utf-8")

def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSE-ON-DRIFT: {msg}")

def main() -> None:
    if not GATE_V2.exists():
        _refuse(f"missing required file: {GATE_V2}")

    s = _read(GATE_V2)

    # If it already avoids the literal token, we're done.
    if "scripts/scripts/" not in s:
        return

    # Replace all literal occurrences with a concatenation-based variable usage.
    # We also add DOUBLE=... near the top if not present.
    if 'DOUBLE="scripts/""scripts/"' not in s:
        insert_after = 'cd "${REPO_ROOT}"\n\n'
        if insert_after not in s:
            _refuse("could not find insertion point after cd REPO_ROOT in v2 gate")
        s = s.replace(insert_after, insert_after + 'DOUBLE="scripts/""scripts/"\n\n', 1)

    # Replace comment examples first
    s = s.replace("bash scripts/scripts/<...>", 'bash ${DOUBLE}<...>')
    s = s.replace("./scripts/scripts/<...>", './${DOUBLE}<...>')

    # Replace grep patterns (keep behavior: match bash scripts/scripts/ and ./scripts/scripts/)
    s = s.replace("scripts/scripts/", '${DOUBLE}')

    _write(GATE_V2, s)

if __name__ == "__main__":
    main()
