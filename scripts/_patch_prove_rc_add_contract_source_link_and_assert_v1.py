from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")
CONTRACT = "docs/contracts/rivalry_chronicle_contract_output_v1.md"

COMMENT = f"# Contract source-of-truth: {CONTRACT}"
ENFORCE_ANCHOR = "# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys."

IMPORT_ANCHOR = "from pathlib import Path"
ASSERT_BLOCK = f"""\
contract_path = os.path.join(os.path.abspath(os.getcwd()), "{CONTRACT}")
if not os.path.exists(contract_path):
    raise SystemExit("ERROR: missing contract source-of-truth at: " + contract_path)
"""

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"REFUSE: missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")

    if ENFORCE_ANCHOR not in text:
        raise SystemExit(f"REFUSE: missing anchor in prove script: {ENFORCE_ANCHOR}")
    if IMPORT_ANCHOR not in text:
        raise SystemExit(f"REFUSE: missing anchor in prove script: {IMPORT_ANCHOR}")

    changed = False

    # Insert comment once
    if COMMENT not in text:
        text = text.replace(ENFORCE_ANCHOR, COMMENT + "\n" + ENFORCE_ANCHOR, 1)
        changed = True

    # Insert assertion once (after pathlib import, but only in the export heredoc context)
    if ASSERT_BLOCK.strip() not in text:
        # Safer: replace first occurrence of import anchor within the export block
        # (the file already shows this import inside the export heredoc)
        repl = IMPORT_ANCHOR + "\n\n" + ASSERT_BLOCK.rstrip() + "\n"
        text = text.replace(IMPORT_ANCHOR, repl, 1)
        changed = True

    if not changed:
        print("OK: prove RC already contains contract source link + presence assertion (v1 idempotent).")
    else:
        PROVE.write_text(text, encoding="utf-8")
        print("OK: inserted contract source link + presence assertion in prove RC (v1).")

if __name__ == "__main__":
    main()
