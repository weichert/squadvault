from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/canonical/Documentation_Map_and_Canonical_References.md")

NEEDLE = "Golden_Path_Production_Freeze_v1.0.md"
INSERT_BLOCK = (
    "\n- **Golden Path production freeze:**  \n"
    "  → [Golden_Path_Production_Freeze_v1.0.md](Golden_Path_Production_Freeze_v1.0.md)\n"
)

ANCHOR = (
    "- **CI + Docs hardening freeze:**  \n"
    "  → [CI_Docs_Hardening_Freeze_v1.0.md](../addenda/CI_Docs_Hardening_Freeze_v1.0.md)\n"
)


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if NEEDLE in txt:
        print("OK: already present (no-op)")
        return

    if ANCHOR not in txt:
        raise SystemExit("ERROR: could not locate Notes anchor (CI + Docs hardening freeze block)")

    out = txt.replace(ANCHOR, ANCHOR + INSERT_BLOCK)
    TARGET.write_text(out, encoding="utf-8")
    print(f"OK: updated {TARGET}")


if __name__ == "__main__":
    main()
