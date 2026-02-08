from __future__ import annotations

from pathlib import Path

PATCHER = Path("scripts/_patch_add_gate_ci_guardrails_ops_entrypoint_parity_v1.py")
GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

def main() -> None:
    if not PATCHER.exists():
        raise SystemExit(f"ERROR: missing {PATCHER}")
    if not GATE.exists():
        raise SystemExit(f"ERROR: missing {GATE}")

    gate_text = GATE.read_text(encoding="utf-8")

    patcher_text = PATCHER.read_text(encoding="utf-8")
    original = patcher_text

    needle = "GATE_TEXT"
    assign_idx = patcher_text.find(needle)
    if assign_idx == -1:
        raise SystemExit("ERROR: cannot find GATE_TEXT in patcher; refuse")

    # Find the assignment start: "GATE_TEXT ="
    line_start = patcher_text.rfind("\n", 0, assign_idx) + 1
    line_end = patcher_text.find("\n", assign_idx)
    if line_end == -1:
        line_end = len(patcher_text)

    # Ensure we're on the GATE_TEXT assignment line
    if "GATE_TEXT" not in patcher_text[line_start:line_end] or "=" not in patcher_text[line_start:line_end]:
        # scan forward to the actual assignment line
        search_from = line_end
        found = False
        for _ in range(0, 2000):
            if search_from >= len(patcher_text):
                break
            next_end = patcher_text.find("\n", search_from)
            if next_end == -1:
                next_end = len(patcher_text)
            line = patcher_text[search_from:next_end]
            if line.strip().startswith("GATE_TEXT") and "=" in line:
                line_start = search_from
                line_end = next_end
                found = True
                break
            search_from = next_end + 1
        if not found:
            raise SystemExit("ERROR: could not locate 'GATE_TEXT =' assignment line; refuse")

    # Find the opening triple-quote delimiter after the '='
    eq_idx = patcher_text.find("=", line_start, line_end)
    if eq_idx == -1:
        raise SystemExit("ERROR: malformed GATE_TEXT assignment line; refuse")

    after_eq = patcher_text[eq_idx+1:line_end]
    if 'r"""' in after_eq:
        open_delim = 'r"""'
    elif '"""' in after_eq:
        open_delim = '"""'
    else:
        # maybe delimiter is on following line(s)
        open_delim = None

    open_idx = patcher_text.find('r"""', eq_idx, eq_idx + 400)
    if open_idx == -1:
        open_idx = patcher_text.find('"""', eq_idx, eq_idx + 400)
    if open_idx == -1:
        raise SystemExit("ERROR: could not find opening triple-quote for GATE_TEXT near assignment; refuse")

    open_delim = 'r"""' if patcher_text.startswith('r"""', open_idx) else '"""'
    content_start = open_idx + len(open_delim)

    close_idx = patcher_text.find('"""', content_start)
    if close_idx == -1:
        raise SystemExit("ERROR: could not find closing triple-quote for GATE_TEXT; refuse")

    current_payload = patcher_text[content_start:close_idx]
    if current_payload == gate_text and open_delim == 'r"""':
        print("OK: add-gate patcher already matches canonical gate text (raw string)")
        return

    replacement = 'GATE_TEXT = r"""' + gate_text + '"""'

    # Replace from start of assignment line through the closing delimiter
    # by replacing the whole assignment block (line_start .. close_idx+3),
    # but keep any trailing text after the close delimiter on the same line (rare).
    after_close = patcher_text[close_idx+3:]
    before = patcher_text[:line_start]

    # If there's non-whitespace between line_start and open_idx, keep structure stable by rewriting only assignment.
    patcher_text = before + replacement + after_close

    if patcher_text == original:
        raise SystemExit("ERROR: no changes applied; refuse")

    PATCHER.write_text(patcher_text, encoding="utf-8")
    print("UPDATED:", PATCHER)

if __name__ == "__main__":
    main()
