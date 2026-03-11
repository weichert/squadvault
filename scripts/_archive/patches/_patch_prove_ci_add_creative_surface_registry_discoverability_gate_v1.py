from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BANNER = 'echo "=== Gate: Creative Surface Registry discoverability (v1) ==="'
CALL = 'bash "${repo_root}/scripts/gate_creative_surface_registry_discoverability_v1.sh"'

# Anchor near the parity gate (present in this repo per your earlier work)
ANCHOR = "gate_creative_surface_registry_parity_v1.sh"


def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"Refusing: missing {PROVE}")

    text = PROVE.read_text(encoding="utf-8")
    if CALL in text:
        return

    lines = text.splitlines(True)

    insert_at = None
    for i, ln in enumerate(lines):
        if ANCHOR in ln:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit("Refusing: could not find parity gate anchor in scripts/prove_ci.sh")

    block = "\n".join([BANNER, CALL]) + "\n"
    lines.insert(insert_at, block)

    PROVE.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
