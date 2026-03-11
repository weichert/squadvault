from __future__ import annotations

import re
from pathlib import Path

GATE = Path("scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh")

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def replace_in_awk_program(program: str) -> str:
    # Guard: only patch if we see scalar assignments or references involving `in`.
    # (Avoid touching an awk program that doesn't use that variable.)
    if "in=" not in program and re.search(r"(?<![A-Za-z0-9_])in(?![A-Za-z0-9_])", program) is None:
        return program

    # Replace standalone identifier `in` -> `in_count`
    # (will transform: in=0, in=1, in==0, { in=1; }, etc.)
    return re.sub(r"(?<![A-Za-z0-9_])in(?![A-Za-z0-9_])", "in_count", program)

def main() -> None:
    if not GATE.exists():
        die(f"missing {GATE}")

    text = GATE.read_text(encoding="utf-8")

    # No-op if already fixed anywhere.
    if re.search(r"BEGIN\s*\{\s*in_count\s*=\s*0\s*\}", text):
        return

    lines = text.splitlines(keepends=True)

    # Find an awk program started via a single quote.
    # We look for a line containing awk ... '  (quote can be at end or mid-line).
    start_i = None
    start_quote_pos = None
    for i, line in enumerate(lines):
        if "awk" not in line:
            continue
        m = re.search(r"\bawk\b[^#\n]*'", line)  # avoid commented-out awk
        if m:
            start_i = i
            # position of first quote after awk
            start_quote_pos = line.find("'", m.start())
            break

    if start_i is None or start_quote_pos is None:
        die("could not find awk invocation that opens a single-quoted awk program (looked for: awk ... ')")

    # Now find the closing single quote that terminates that awk program.
    # It might be:
    #   - on its own line:   '
    #   - at end of some line: ... '
    #   - followed by pipes:  ' | sort -u
    end_i = None
    end_quote_pos = None

    # If the opening quote line also contains a closing quote later on the same line,
    # that's a one-liner awk program.
    rest = lines[start_i][start_quote_pos + 1 :]
    if "'" in rest:
        end_i = start_i
        end_quote_pos = start_quote_pos + 1 + rest.find("'")
    else:
        for j in range(start_i + 1, len(lines)):
            if "'" in lines[j]:
                end_i = j
                end_quote_pos = lines[j].find("'")
                break

    if end_i is None or end_quote_pos is None:
        die("found awk opening quote but could not find closing quote to terminate awk program")

    # Extract awk program content between the quotes.
    if start_i == end_i:
        program = lines[start_i][start_quote_pos + 1 : end_quote_pos]
        new_program = replace_in_awk_program(program)
        if new_program == program:
            die("awk program found but no 'in' tokens replaced; refusing (unexpected)")
        lines[start_i] = (
            lines[start_i][: start_quote_pos + 1] + new_program + lines[start_i][end_quote_pos:]
        )
    else:
        program_parts = []
        program_parts.append(lines[start_i][start_quote_pos + 1 :])
        for k in range(start_i + 1, end_i):
            program_parts.append(lines[k])
        program_parts.append(lines[end_i][:end_quote_pos])
        program = "".join(program_parts)

        new_program = replace_in_awk_program(program)
        if new_program == program:
            die("awk program found but no 'in' tokens replaced; refusing (unexpected)")

        # Rebuild:
        # - keep opening line up to quote
        # - replace entire middle with new program
        # - keep end line from closing quote onward
        opening_prefix = lines[start_i][: start_quote_pos + 1]
        closing_suffix = lines[end_i][end_quote_pos:]  # includes the closing quote and anything after it

        new_block = opening_prefix + new_program + closing_suffix

        # Replace the range [start_i, end_i] with a single line block.
        lines[start_i : end_i + 1] = [new_block]

    new_text = "".join(lines)
    if new_text == text:
        return

    GATE.write_text(new_text, encoding="utf-8")

if __name__ == "__main__":
    main()
