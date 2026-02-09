from __future__ import annotations

import re
from pathlib import Path

ADD_PATCHER = Path("scripts/_patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.py")
GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def replace_embedded(truth: str, text: str) -> str:
    """
    Replace the first embedded CANON/GATE_TEXT triple-quoted block in ADD_PATCHER
    with the exact on-disk gate text.

    Supports:
      CANON = r'''...'''
      CANON = '''...'''
      CANON = r\"\"\"...\"\"\"
      CANON = \"\"\"...\"\"\"
      (same for GATE_TEXT)
    """
    patterns = [
        (r"(?s)^(CANON|GATE_TEXT)\s*=\s*r'''[\s\S]*?'''\s*\n", "raw_single"),
        (r"(?s)^(CANON|GATE_TEXT)\s*=\s*'''[\s\S]*?'''\s*\n", "triple_single"),
        (r'(?s)^(CANON|GATE_TEXT)\s*=\s*r"""[\s\S]*?"""\s*\n', "raw_double"),
        (r'(?s)^(CANON|GATE_TEXT)\s*=\s*"""[\s\S]*?"""\s*\n', "triple_double"),
    ]

    for pat, kind in patterns:
        m = re.search(pat, text, flags=re.M)
        if not m:
            continue

        var = m.group(1)

        if kind == "raw_single":
            new_block = f"{var} = r'''{truth}'''\n"
        elif kind == "triple_single":
            safe = truth.replace("'''", r"\'\'\'")
            new_block = f"{var} = '''{safe}'''\n"
        elif kind == "raw_double":
            safe = truth.replace('"""', r'\"\"\"')
            new_block = f'{var} = r"""{safe}"""\n'
        else:  # triple_double
            safe = truth.replace('"""', r'\"\"\"')
            new_block = f'{var} = """{safe}"""\n'

        return text[: m.start()] + new_block + text[m.end() :]

    die("could not locate embedded CANON/GATE_TEXT triple-quoted block in add-gate patcher")

def main() -> None:
    if not ADD_PATCHER.exists():
        die(f"missing {ADD_PATCHER}")
    if not GATE.exists():
        die(f"missing {GATE}")

    gate_text = GATE.read_text(encoding="utf-8")
    ptxt = ADD_PATCHER.read_text(encoding="utf-8")

    ptxt2 = replace_embedded(gate_text, ptxt)
    if ptxt2 == ptxt:
        return

    ADD_PATCHER.write_text(ptxt2, encoding="utf-8")

if __name__ == "__main__":
    main()
