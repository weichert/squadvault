from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py")

KEY = "scripts/gate_contracts_index_discoverability_v1.sh"
VAL = "Enforce docs/contracts/README.md indexes all versioned contracts (v1)"

# Match:
#   DESC = {
#   DESC: dict[str,str] = {
#   DESC: Dict[str,str] = {  # etc.
DESC_OPEN_RE = re.compile(r'^\s*DESC\b.*=\s*\{')  # allow annotations + trailing content
PAIR_RE = re.compile(r'^(?P<indent>\s*)"(?P<k>[^"]+)"\s*:\s*"(?P<v>[^"]*)"\s*,?\s*$')

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    lines = TARGET.read_text(encoding="utf-8").splitlines(True)

    start_line = None
    brace_depth = 0
    for i, ln in enumerate(lines):
        if DESC_OPEN_RE.match(ln):
            start_line = i
            brace_depth = ln.count("{") - ln.count("}")
            break

    if start_line is None:
        raise SystemExit("Refusing: could not find DESC dict assignment line (expected `DESC ... = {`).")

    end_line = None
    for j in range(start_line + 1, len(lines)):
        brace_depth += lines[j].count("{") - lines[j].count("}")
        if brace_depth <= 0:
            end_line = j
            break

    if end_line is None:
        raise SystemExit("Refusing: could not find end of DESC dict (unbalanced braces).")

    body = lines[start_line + 1 : end_line]

    pairs: dict[str, str] = {}
    indent = "    "
    kept_other_lines: list[str] = []

    for ln in body:
        m = PAIR_RE.match(ln)
        if not m:
            kept_other_lines.append(ln)
            continue
        indent = m.group("indent") or indent
        pairs[m.group("k")] = m.group("v")

    if pairs.get(KEY) == VAL:
        return

    pairs[KEY] = VAL

    rendered = [f'{indent}"{k}": "{pairs[k]}",\n' for k in sorted(pairs.keys())]
    new_body = rendered + kept_other_lines

    new_lines = lines[: start_line + 1] + new_body + lines[end_line:]
    TARGET.write_text("".join(new_lines), encoding="utf-8")

if __name__ == "__main__":
    main()
