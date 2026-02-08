from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_ci_registry_execution_alignment_v1.sh")

BEGIN = "# SV_PATCH: exclude prove_ci from gate sets (v1) begin"
END = "# SV_PATCH: exclude prove_ci from gate sets (v1) end"

BLOCK = "\n".join(
    [
        BEGIN,
        "",
        "# Exclude orchestrator (prove_ci.sh) from all derived sets.",
        "# This gate is about *proof runners* registered in the registry vs invoked by prove_ci.sh.",
        'filter_out_prove_ci() {',
        '  # $1 = file; $2 = mode ("plain" or "cond")',
        '  f="$1"',
        '  mode="${2:-plain}"',
        '  if [[ ! -f "$f" ]]; then',
        '    return',
        '  fi',
        '  if [[ "$mode" = "cond" ]]; then',
        '    # lines like: <line>:scripts/prove_foo.sh',
        '    grep -vE ":scripts/prove_ci\\.sh$" "$f" > "${f}.tmp" || true',
        '  else',
        '    grep -vE "^scripts/prove_ci\\.sh$" "$f" > "${f}.tmp" || true',
        '  fi',
        '  mv "${f}.tmp" "$f"',
        '}',
        "",
        "# Apply to all sets we derive.",
        'filter_out_prove_ci "${R_ALL}" plain',
        'filter_out_prove_ci "${X_EXEMPT}" plain',
        'filter_out_prove_ci "${COND_ALLOW}" plain',
        'filter_out_prove_ci "${E_ALL}" plain',
        'filter_out_prove_ci "${E_UNCOND}" plain',
        'filter_out_prove_ci "${E_COND}" cond',
        "",
        END,
        "",
    ]
)

ANCHOR = 'if [[ ! -s "${E_ALL}" ]]; then'


def main() -> None:
    if not GATE.exists():
        raise SystemExit(f"ERROR: missing {GATE}")

    text = GATE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        return  # idempotent

    if ANCHOR not in text:
        raise SystemExit(
            "ERROR: canonical anchor not found in gate script:\n"
            f"  expected: {ANCHOR}\n"
            "Refusing to guess insertion point (fail-closed)."
        )

    lines = text.splitlines(True)
    out: list[str] = []
    inserted = False

    for line in lines:
        if (not inserted) and (ANCHOR in line):
            out.append(BLOCK)
            inserted = True
        out.append(line)

    if not inserted:
        raise SystemExit("ERROR: failed to insert exclusion block (unexpected)")

    GATE.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
