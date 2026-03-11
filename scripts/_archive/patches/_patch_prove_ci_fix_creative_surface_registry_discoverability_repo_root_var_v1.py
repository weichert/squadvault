from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

OLD = 'bash "${repo_root}/scripts/gate_creative_surface_registry_discoverability_v1.sh"'
NEW = 'bash "${repo_root_for_gate}/scripts/gate_creative_surface_registry_discoverability_v1.sh"'


def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"Refusing: missing {PROVE}")

    txt = PROVE.read_text(encoding="utf-8")
    if NEW in txt:
        return
    if OLD not in txt:
        raise SystemExit("Refusing: expected discoverability gate invocation not found (prove_ci may have drifted).")

    PROVE.write_text(txt.replace(OLD, NEW), encoding="utf-8")


if __name__ == "__main__":
    main()
