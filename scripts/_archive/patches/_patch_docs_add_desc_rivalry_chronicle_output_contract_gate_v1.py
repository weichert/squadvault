from __future__ import annotations

import re
from pathlib import Path

TARGET = Path("scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py")

KEY = "scripts/gate_rivalry_chronicle_output_contract_v1.sh"
VAL = "Enforce Rivalry Chronicle export conforms to output contract (v1)"

# Match both:
#   DESC = {
#   DESC: dict[str, str] = {
DESC_OPEN_RE = re.compile(r'^\s*DESC\b.*=\s*\{')
PAIR_RE = re.compile(r'^(?P<indent>\s*)"(?P<k>[^"]+)"\s*:\s*"(?P<v>[^"]*)"\s*,?\s*$')

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    lines = TARGET.read_text(encoding="utf-8").splitlines(True)

    start = None
    brace_depth = 0
    for i, ln in enumerate(lines):
        if DESC_OPEN_RE.match(ln):
            start = i
            brace_depth = ln.count("{") - ln.count("}")
            break
    if start is None:
        raise SystemExit("Refusing: could not find DESC dict assignment line.")

    end = None
    for j in range(start + 1, len(lines)):
        brace_depth += lines[j].count("{") - lines[j].count("}")
        if brace_depth <= 0:
            end = j
            break
    if end is None:
        raise SystemExit("Refusing: could not find end of DESC dict (unbalanced braces).")

    body = lines[start + 1 : end]

    pairs: dict[str, str] = {}
    indent = "    "
    kept_other: list[str] = []

    for ln in body:
        m = PAIR_RE.match(ln)
        if not m:
            kept_other.append(ln)
            continue
        indent = m.group("indent") or indent
        pairs[m.group("k")] = m.group("v")

    if pairs.get(KEY) == VAL:
        return

    pairs[KEY] = VAL

    rendered = [f'{indent}"{k}": "{pairs[k]}",\n' for k in sorted(pairs.keys())]
    new_body = rendered + kept_other

    out = lines[: start + 1] + new_body + lines[end:]
    TARGET.write_text("".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
