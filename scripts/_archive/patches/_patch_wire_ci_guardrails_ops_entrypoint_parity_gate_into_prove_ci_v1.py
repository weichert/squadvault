from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

ANCHOR = "==> Gate: CI Guardrails ops entrypoints section + TOC (v2)"

BEGIN = "# SV_GATE: ci_guardrails_ops_entrypoint_parity (v1) begin"
END = "# SV_GATE: ci_guardrails_ops_entrypoint_parity (v1) end"

BLOCK = f"""\
{BEGIN}
bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh
{END}
"""

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"ERROR: missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        print("OK: parity gate already wired into prove_ci")
        return

    if ANCHOR in text:
        # Insert immediately after the anchor line.
        lines = text.splitlines(True)
        out: list[str] = []
        inserted = False
        for line in lines:
            out.append(line)
            if (not inserted) and (ANCHOR in line):
                # Ensure there's a trailing newline before inserting
                if not line.endswith("\n"):
                    out.append("\n")
                out.append(BLOCK)
                inserted = True
        if not inserted:
            raise SystemExit("ERROR: failed to insert after anchor despite anchor presence")
        PROVE.write_text("".join(out), encoding="utf-8")
        print("UPDATED: wired parity gate into prove_ci after anchor:", ANCHOR)
        return

    # Fallback: insert after docs gates but before proof suite execution.
    # We choose a conservative fail-closed location: after docs integrity gates typically run,
    # before the proof suite is executed.
    #
    # Heuristic anchor: first occurrence of "==> Proof suite" (or similar).
    fallback_anchor_candidates = [
        "==> Proof suite",
        "==> Prove suite",
        "==> Proofs",
    ]

    for cand in fallback_anchor_candidates:
        if cand in text:
            lines = text.splitlines(True)
            out = []
            inserted = False
            for line in lines:
                if (not inserted) and (cand in line):
                    out.append(BLOCK)
                    inserted = True
                out.append(line)
            if not inserted:
                raise SystemExit("ERROR: failed to insert before fallback anchor")
            PROVE.write_text("".join(out), encoding="utf-8")
            print("UPDATED: wired parity gate into prove_ci before fallback anchor:", cand)
            return

    raise SystemExit(
        "ERROR: could not find canonical insertion point (anchor or fallback). "
        "Refuse to guess."
    )

if __name__ == "__main__":
    main()
