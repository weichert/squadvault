from __future__ import annotations

from pathlib import Path

TARGETS = [
    Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"),
    Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"),
]

BEGIN = "<!-- SV_CONTRACT_SURFACE_PROOFS_v1_BEGIN -->"
END = "<!-- SV_CONTRACT_SURFACE_PROOFS_v1_END -->"

ENTRY = "- scripts/prove_contract_surface_autosync_noop_v1.sh — Proof: Contract surface autosync is a no-op on canonical repo (v1)\n"

SECTION_HEADER = (
    "\n"
    "## Contract Surface Proofs\n\n"
    f"{BEGIN}\n"
    f"{END}\n"
)

def upsert_section(path: Path, text: str) -> str:
    if BEGIN in text and END in text:
        return text
    # Append a dedicated section at end (deterministic).
    if not text.endswith("\n"):
        text += "\n"
    return text + SECTION_HEADER

def insert_entry(text: str) -> str:
    if ENTRY.strip() in text:
        return text

    if BEGIN not in text or END not in text:
        raise SystemExit("FAIL: section markers missing after upsert (unexpected).")

    before, rest = text.split(BEGIN, 1)
    middle, after = rest.split(END, 1)

    # Insert immediately before END marker, preserving existing middle content.
    if not middle.endswith("\n"):
        middle += "\n"
    middle_out = middle + ENTRY

    return before + BEGIN + middle_out + END + after

def main() -> int:
    changed_any = False

    for p in TARGETS:
        if not p.exists():
            raise SystemExit(f"FAIL: missing target doc: {p}")

        original = p.read_text(encoding="utf-8")
        s = upsert_section(p, original)
        s2 = insert_entry(s)

        if s2 != original:
            p.write_text(s2, encoding="utf-8")
            changed_any = True
            print(f"OK: updated {p}")
        else:
            print(f"OK: no change needed for {p}")

    if not changed_any:
        print("OK: docs already contained entry.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
