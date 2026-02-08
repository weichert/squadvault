from __future__ import annotations

from pathlib import Path
import re

PATCHER = Path("scripts/_patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.py")
GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

def py_triple_quote(s: str) -> str:
    # Safe for """...""" as long as content doesn't contain """ (it doesn't).
    return '"""' + s.replace('"""', r'\"\"\"') + '"""'

def main() -> None:
    if not PATCHER.exists():
        raise SystemExit(f"ERROR: missing {PATCHER}")
    if not GATE.exists():
        raise SystemExit(f"ERROR: missing {GATE}")

    gate_text = GATE.read_text(encoding="utf-8")
    patcher_text = PATCHER.read_text(encoding="utf-8")

    # Find the GATE_TEXT assignment block.
    m = re.search(r'(?s)^GATE_TEXT\s*=\s*"""(.*?)"""\s*$', patcher_text, flags=re.MULTILINE)
    if not m:
        raise SystemExit("ERROR: could not find GATE_TEXT triple-quoted block in patcher; refuse")

    current_embedded = m.group(1)
    if current_embedded == gate_text:
        print("OK: add-gate patcher already matches canonical gate text")
        return

    new_block = "GATE_TEXT = " + py_triple_quote(gate_text)
    new_text = patcher_text[: m.start()] + new_block + patcher_text[m.end() :]

    PATCHER.write_text(new_text, encoding="utf-8")
    print("UPDATED:", PATCHER)

if __name__ == "__main__":
    main()
