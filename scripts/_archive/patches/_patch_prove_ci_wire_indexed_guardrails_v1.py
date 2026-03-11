from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"

# We’ll insert these *before* the parity gate is run (so parity reflects them as executed).
# Anchor on the existing parity gate invocation line.
ANCHOR = "bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"

INSERT = [
    "\n",
    "## Indexed guardrails: execute to maintain ops index ↔ prove_ci parity\n",
    "bash scripts/gate_no_test_dir_case_drift_v1.sh\n",
    "bash scripts/gate_standard_show_input_need_coverage_v1.sh\n",
]

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")
    if ANCHOR not in text:
        raise SystemExit("ERROR: expected parity gate invocation anchor not found in scripts/prove_ci.sh")

    if "bash scripts/gate_no_test_dir_case_drift_v1.sh\n" in text and "bash scripts/gate_standard_show_input_need_coverage_v1.sh\n" in text:
        print("OK: prove_ci already wires both guardrails (idempotent).")
        return

    parts = text.split(ANCHOR)
    if len(parts) != 2:
        raise SystemExit("ERROR: unexpected multiple parity gate anchors; refusing to patch.")

    before, after = parts

    # Ensure insertions appear once (even if one already exists).
    add_lines = []
    for ln in INSERT:
        if ln.strip() and ln in before:
            continue
        add_lines.append(ln)

    new_text = before + "".join(add_lines) + ANCHOR + after
    PROVE.write_text(new_text, encoding="utf-8")
    print("OK: wired indexed guardrails into prove_ci before parity gate.")

if __name__ == "__main__":
    main()
