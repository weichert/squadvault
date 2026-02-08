from __future__ import annotations

from pathlib import Path

P = Path("scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py")

KEY = "scripts/gate_proof_surface_registry_excludes_gates_v1.sh"
VAL = "Gate vs proof boundary: enforce Proof Surface Registry excludes scripts/gate_*.sh (v1)"


def _find_matching_brace(text: str, open_idx: int) -> int:
    # open_idx points at '{'
    depth = 0
    in_squote = False
    in_dquote = False
    esc = False

    for i in range(open_idx, len(text)):
        ch = text[i]

        if esc:
            esc = False
            continue

        if ch == "\\":
            esc = True
            continue

        if in_squote:
            if ch == "'":
                in_squote = False
            continue

        if in_dquote:
            if ch == '"':
                in_dquote = False
            continue

        if ch == "'":
            in_squote = True
            continue
        if ch == '"':
            in_dquote = True
            continue

        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                return i

    raise SystemExit("ERROR: could not find matching '}' for target dict; refusing to patch.")


def main() -> None:
    txt = P.read_text(encoding="utf-8")

    if KEY in txt:
        print("OK: descriptions already include proof-registry-excludes-gates (v4 no-op)")
        return

    # Find any existing scripts/ key usage (single or double quotes)
    pos = txt.find('"scripts/')
    if pos == -1:
        pos = txt.find("'scripts/")
    if pos == -1:
        raise SystemExit(
            "ERROR: could not find any existing 'scripts/' keys in target file; "
            "cannot locate canonical descriptions structure safely."
        )

    # Find the nearest preceding '{' before that key occurrence
    open_idx = txt.rfind("{", 0, pos)
    if open_idx == -1:
        raise SystemExit("ERROR: could not find '{' before scripts/ key; refusing to patch.")

    close_idx = _find_matching_brace(txt, open_idx)

    # Determine indentation by looking at the first non-empty line after the opening brace
    after = txt[open_idx + 1 : close_idx]
    lines = after.splitlines()

    indent = "    "  # default 4 spaces
    for ln in lines:
        if ln.strip():
            indent = ln[: len(ln) - len(ln.lstrip())]
            break

    entry = f'{indent}"{KEY}": "{VAL}",\n'

    # Insert immediately after the opening brace, ensuring a newline if needed
    insert_at = open_idx + 1
    if insert_at < len(txt) and txt[insert_at] != "\n":
        entry = "\n" + entry

    out = txt[:insert_at] + entry + txt[insert_at:]
    P.write_text(out, encoding="utf-8")
    print("OK: inserted descriptions entry into canonical dict block (v4)")


if __name__ == "__main__":
    main()
