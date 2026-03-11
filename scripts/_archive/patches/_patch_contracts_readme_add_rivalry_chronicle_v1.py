from __future__ import annotations

from pathlib import Path

README = Path("docs/contracts/README.md")

LINE = "- Rivalry Chronicle Output Contract (v1): rivalry_chronicle_output_contract_v1.md"

def normalize(s: str) -> str:
    return s.replace("\r\n", "\n")

def main() -> None:
    if not README.exists():
        raise SystemExit(f"ERROR: expected {README} to exist.")

    s = normalize(README.read_text(encoding="utf-8"))

    if "rivalry_chronicle_output_contract_v1.md" in s:
        print("OK: contracts README already references Rivalry Chronicle contract.")
        return

    # Insert near top under a Contracts list if present; otherwise append.
    lines = s.splitlines(True)
    out = []
    inserted = False

    for i, l in enumerate(lines):
        out.append(l)
        if not inserted and l.strip().lower() in ("## contracts", "# contracts"):
            # Add after header line
            out.append("\n")
            out.append(LINE + "\n")
            inserted = True

    if not inserted:
        if not s.endswith("\n"):
            out.append("\n")
        out.append("\n" + LINE + "\n")

    README.write_text("".join(out), encoding="utf-8")
    print(f"OK: updated {README} with Rivalry Chronicle reference.")

if __name__ == "__main__":
    main()
