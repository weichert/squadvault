from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

ANCHOR = "# === /SV_ANCHOR: docs_gates (v1) ==="

BEGIN = "# SV_GATE: proof_suite_completeness (v1) begin"
END = "# SV_GATE: proof_suite_completeness (v1) end"

BLOCK = f"""\
{BEGIN}
echo "==> Proof suite completeness gate (v1)"
bash scripts/gate_proof_suite_completeness_v1.sh
{END}
"""

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"ERROR: missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    # Idempotent: already patched -> no-op
    if BEGIN in text and END in text:
        return

    lines = text.splitlines(True)  # keep newlines
    try:
        i = next(idx for idx, line in enumerate(lines) if ANCHOR in line)
    except StopIteration:
        raise SystemExit(f"ERROR: insertion anchor not found in {PROVE}: {ANCHOR!r}")

    # Insert immediately AFTER the anchor line.
    insert_at = i + 1
    insertion = BLOCK + "\n"
    lines.insert(insert_at, insertion)

    PROVE.write_text("".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
