from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_eal_calibration_type_a_v1.sh")

# Remove ONLY the first invocation; keep the later quoted array invocation.
NEEDLE = "./scripts/py -m pytest -q ${tests_list}\n"


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if NEEDLE not in s:
        print("OK: redundant pytest run already removed (v1) or upstream changed.")
        return

    TARGET.write_text(s.replace(NEEDLE, "", 1), encoding="utf-8")
    print("OK: removed redundant first pytest run in prove_eal_calibration (v1).")


if __name__ == "__main__":
    main()
