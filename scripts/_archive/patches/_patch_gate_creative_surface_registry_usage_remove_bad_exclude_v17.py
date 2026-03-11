from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gate_creative_surface_registry_usage_v1.sh")

BAD = ' --exclude="gate_creative_surface_registry_usage_v1.sh"'
BAD2 = " --exclude=gate_creative_surface_registry_usage_v1.sh"

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    src = TARGET.read_text(encoding="utf-8")

    if BAD not in src and BAD2 not in src:
        print("OK: no injected --exclude present (noop)")
        return

    out = src.replace(BAD, "").replace(BAD2, "")
    TARGET.write_text(out, encoding="utf-8")
    print("OK: removed injected --exclude from gate script (v17)")

if __name__ == "__main__":
    main()
