from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py")

KEY = "gate_creative_surface_registry_discoverability_v1.sh"
DESC = "Creative Surface Registry must be discoverable from CI guardrails ops index (fail-closed)."

ANCHOR = "gate_creative_surface_registry_parity_v1.sh"


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Refusing: missing {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")
    if KEY in txt:
        return

    lines = txt.splitlines(True)

    insert_at = None
    for i, ln in enumerate(lines):
        if ANCHOR in ln:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit("Refusing: could not find parity gate key anchor in autofill DESC patcher.")

    lines.insert(insert_at, f'    "{KEY}": "{DESC}",\n')
    TARGET.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
