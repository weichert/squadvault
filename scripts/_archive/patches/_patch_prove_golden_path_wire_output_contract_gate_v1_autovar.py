from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_golden_path.sh")

BEGIN = "# SV_GATE: golden_path_output_contract (v1) begin"
END = "# SV_GATE: golden_path_output_contract (v1) end"

def find_selected_var(lines: list[str]) -> tuple[int, str] | None:
    pat = re.compile(
        r"Selected assembly:\s*(?:\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*))"
    )
    for i, line in enumerate(lines):
        if "Selected assembly" not in line:
            continue
        m = pat.search(line)
        if not m:
            continue
        var = m.group(1) or m.group(2)
        return (i, var)
    return None

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")
    if BEGIN in text and END in text:
        return  # idempotent

    lines = text.splitlines(True)
    hit = find_selected_var(lines)
    if hit is None:
        raise SystemExit(
            "Refusing: could not find a 'Selected assembly:' line that references a shell variable "
            "(expected $VAR or ${VAR})."
        )

    idx, var = hit

    block = (
        f"{BEGIN}\n"
        f'echo "== Output contract gate (v1) ==" \n'
        f"bash scripts/gate_golden_path_output_contract_v1.sh --selected-assembly \"${{{var}}}\"\n"
        f"{END}\n"
    )

    insert_at = idx + 1
    PROVE.write_text("".join(lines[:insert_at] + [block] + lines[insert_at:]), encoding="utf-8")

if __name__ == "__main__":
    main()
