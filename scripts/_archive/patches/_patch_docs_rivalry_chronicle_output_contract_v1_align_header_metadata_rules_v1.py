from __future__ import annotations

from pathlib import Path

DOC = Path("docs/contracts/rivalry_chronicle_contract_output_v1.md")
README = Path("docs/contracts/README.md")

HEADER = "# Rivalry Chronicle (v1)"
README_LINE = "- `docs/contracts/rivalry_chronicle_contract_output_v1.md`"

DOC_CANON = """# Rivalry Chronicle (v1)

League ID: <LEAGUE_ID>
Season: <SEASON>
Week: <WEEK>
State: <STATE>
Artifact Type: RIVALRY_CHRONICLE_V1

## Matchup Summary

## Key Moments

## Stats & Nuggets

## Closing

## Metadata rules

Metadata is a contiguous block of `Key: Value` lines immediately after header (optionally after one blank line).

Required keys:
- League ID
- Season
- Week
- State
- Artifact Type

Artifact Type must be `RIVALRY_CHRONICLE_V1`.

## Normalization rules

- Leading blank lines dropped.
- Header must be first line.
- Metadata upsert semantics: key uniqueness; last-write wins / overwrite.
- If required headings are missing, exporter may append a minimal scaffold (blank line separated).
"""

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"REFUSE: missing contract doc: {DOC}")
    if not README.exists():
        raise SystemExit(f"REFUSE: missing contracts README: {README}")

    changed = False

    cur = DOC.read_text(encoding="utf-8")
    if "Rivalry Chronicle" not in cur:
        raise SystemExit("REFUSE: contract doc does not look like Rivalry Chronicle contract")

    if cur != DOC_CANON:
        DOC.write_text(DOC_CANON, encoding="utf-8")
        changed = True

    # README: ensure line exists exactly once (keep existing formatting)
    r = README.read_text(encoding="utf-8")
    count = r.count("`docs/contracts/rivalry_chronicle_contract_output_v1.md`")
    if count > 1:
        raise SystemExit("REFUSE: docs/contracts/README.md references Rivalry Chronicle contract more than once")
    if count == 1:
        # normalize the exact line if needed
        lines = r.splitlines()
        normed = False
        for i, ln in enumerate(lines):
            if "docs/contracts/rivalry_chronicle_contract_output_v1.md" in ln and ln.strip() != README_LINE:
                lines[i] = README_LINE
                normed = True
        if normed:
            README.write_text("\n".join(lines) + ("\n" if r.endswith("\n") else ""), encoding="utf-8")
            changed = True
    else:
        # insert after "## Contract Documents" block by appending within that list
        anchor = "## Contract Documents"
        if anchor not in r:
            raise SystemExit("REFUSE: README anchor missing: '## Contract Documents'")
        # find first contract bullet list start
        lines = r.splitlines(True)
        out = []
        inserted = False
        in_list = False
        for ln in lines:
            out.append(ln)
            if ln.strip() == anchor:
                in_list = True
                continue
            if in_list and ln.startswith("- `docs/contracts/") and not inserted:
                # insert just before the first existing bullet so list stays grouped
                out.pop()
                out.append(README_LINE + "\n")
                out.append(ln)
                inserted = True
                in_list = False
        if not inserted:
            # fallback: append at end of contract documents list
            if "## Indexing Rules" not in r:
                raise SystemExit("REFUSE: README missing expected section: '## Indexing Rules (enforced)'")
            out_text = "".join(out)
            out_text = out_text.replace("## Indexing Rules (enforced)", README_LINE + "\n\n## Indexing Rules (enforced)", 1)
            README.write_text(out_text, encoding="utf-8")
            changed = True
        else:
            README.write_text("".join(out), encoding="utf-8")
            changed = True

    if not changed:
        print("OK: Rivalry Chronicle contract doc already canonical to new spec (v1 idempotent).")
    else:
        print("OK: Rivalry Chronicle contract doc aligned to new spec (v1).")

if __name__ == "__main__":
    main()
