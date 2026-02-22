from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
NEEDLE = "scripts/gate_creative_surface_registry_discoverability_v1.sh"
ANCHOR = "scripts/gate_creative_surface_registry_parity_v1.sh"


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"Refusing: missing {INDEX}")

    txt = INDEX.read_text(encoding="utf-8")
    if NEEDLE in txt:
        return

    lines = txt.splitlines(True)

    insert_at = None
    for i, ln in enumerate(lines):
        if ANCHOR in ln:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit("Refusing: could not find parity gate bullet anchor in CI_Guardrails_Index_v1.0.md")

    lines.insert(insert_at, f"- {NEEDLE}\n")
    INDEX.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
