from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: ops_indices_no_autofill_placeholders (v1) begin"
END = "# SV_GATE: ops_indices_no_autofill_placeholders (v1) end"

BLOCK = f"""\
{BEGIN}
echo "==> Gate: Ops indices must not contain autofill placeholders (v1)"
bash scripts/gate_ops_indices_no_autofill_placeholders_v1.sh
{END}
"""

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"ERROR: missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        # Ensure block is canonical (replace in-place if needed).
        pre = text.split(BEGIN, 1)[0]
        post = text.split(END, 1)[1]
        new_text = pre + BLOCK + post
        if new_text != text:
            PROVE.write_text(new_text, encoding="utf-8")
            print("UPDATED:", PROVE, "(re-canonicalized existing block)")
        else:
            print("OK: prove_ci already contains canonical ops-indices autofill gate block")
        return

    if BEGIN in text or END in text:
        raise SystemExit("ERROR: prove_ci contains only one marker; refuse ambiguous state")

    # Insert near other docs-related gates if possible; otherwise append near the end of the proof suite section.
    anchor = '==> Docs integrity gate (v2)'
    idx = text.find(anchor)
    if idx == -1:
        # Fallback: insert before the "==> unit tests" section if present
        anchor2 = '==> unit tests'
        idx2 = text.find(anchor2)
        if idx2 == -1:
            # Fallback: append at end
            new_text = text.rstrip() + "\n\n" + BLOCK + "\n"
        else:
            new_text = text[:idx2] + BLOCK + "\n" + text[idx2:]
    else:
        # Insert immediately before docs integrity gate header line
        new_text = text[:idx] + BLOCK + "\n" + text[idx:]

    PROVE.write_text(new_text, encoding="utf-8")
    print("UPDATED:", PROVE)

if __name__ == "__main__":
    main()
