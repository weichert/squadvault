from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: allowlist_patchers_insert_sorted (v1) begin"
END = "# SV_GATE: allowlist_patchers_insert_sorted (v1) end"

BLOCK = f"""\
{BEGIN}
echo "==> Gate: allowlist patchers must insert-sorted (v1)"
bash scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh
{END}
"""

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"ERROR: missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        pre = text.split(BEGIN, 1)[0]
        post = text.split(END, 1)[1]
        new_text = pre + BLOCK + post
        if new_text != text:
            PROVE.write_text(new_text, encoding="utf-8")
            print("UPDATED:", PROVE, "(re-canonicalized existing block)")
        else:
            print("OK: prove_ci already contains canonical insert-sorted gate block")
        return

    if BEGIN in text or END in text:
        raise SystemExit("ERROR: prove_ci contains only one marker; refuse ambiguous state")

    # Insert near the idempotence allowlist gate to keep related items together.
    anchor = '==> Gate: patch wrapper idempotence (allowlist) v1'
    idx = text.find(anchor)
    if idx == -1:
        # fallback: insert before docs integrity gate if present
        anchor2 = '==> Docs integrity gate (v2)'
        idx2 = text.find(anchor2)
        if idx2 == -1:
            new_text = text.rstrip() + "\n\n" + BLOCK + "\n"
        else:
            new_text = text[:idx2] + BLOCK + "\n" + text[idx2:]
    else:
        # insert immediately after the anchor line
        nl = text.find("\n", idx)
        if nl == -1:
            new_text = text.rstrip() + "\n" + BLOCK + "\n"
        else:
            new_text = text[:nl+1] + BLOCK + "\n" + text[nl+1:]

    PROVE.write_text(new_text, encoding="utf-8")
    print("UPDATED:", PROVE)

if __name__ == "__main__":
    main()
