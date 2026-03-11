from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_index_creative_surface_registry_discoverability_v1.sh")

OLD = 'snippet="`docs/80_indices/ops/Creative_Surface_Registry_v1.0.md`"\n'
NEW = 'snippet="\\`docs/80_indices/ops/Creative_Surface_Registry_v1.0.md\\`"\n'


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Refusing: missing {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")
    if NEW in txt:
        return
    if OLD not in txt:
        raise SystemExit("Refusing: expected snippet line not found (wrapper may have drifted).")

    TARGET.write_text(txt.replace(OLD, NEW), encoding="utf-8")


if __name__ == "__main__":
    main()
