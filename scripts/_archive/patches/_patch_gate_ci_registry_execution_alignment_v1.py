from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: ci_registry_execution_alignment (v1) begin"
END = "# SV_GATE: ci_registry_execution_alignment (v1) end"

BLOCK = "\n".join(
    [
        BEGIN,
        'echo "==> Gate: CI registry → execution alignment (v1)"',
        "bash scripts/gate_ci_registry_execution_alignment_v1.sh",
        END,
        "",
    ]
)

# Canonical insertion anchor: immediately after Proof Suite Completeness Gate (v1) end marker
ANCHOR = "# SV_GATE: proof_suite_completeness (v1) end"


def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"ERROR: missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        # already present, idempotent
        return

    if ANCHOR not in text:
        raise SystemExit(
            "ERROR: canonical insertion anchor not found in scripts/prove_ci.sh:\n"
            f"  expected line containing: {ANCHOR}\n"
            "Refusing to guess insertion point (fail-closed)."
        )

    lines = text.splitlines(True)  # keep newlines
    out: list[str] = []

    inserted = False
    for line in lines:
        out.append(line)
        if (not inserted) and (ANCHOR in line):
            # insert immediately after the anchor line
            # ensure there's exactly one newline before block if needed
            if len(out) >= 1 and not out[-1].endswith("\n"):
                out[-1] = out[-1] + "\n"
            out.append(BLOCK)
            inserted = True

    if not inserted:
        raise SystemExit("ERROR: failed to insert block (unexpected)")

    PROVE.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
