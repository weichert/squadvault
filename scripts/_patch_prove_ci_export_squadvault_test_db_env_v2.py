from __future__ import annotations
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

OLD = "export SQUADVAULT_TEST_DB\n"
NEW = 'export SQUADVAULT_TEST_DB="${WORK_DB}"\n'

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if NEW in s:
        print("OK: prove_ci.sh already exports SQUADVAULT_TEST_DB from WORK_DB; no-op.")
        return

    if OLD not in s:
        raise SystemExit(
            "ERROR: expected exact line not found: 'export SQUADVAULT_TEST_DB'.\n"
            "Refusing to guess. (Has prove_ci.sh drifted?)"
        )

    s2 = s.replace(OLD, NEW, 1)
    TARGET.write_text(s2, encoding="utf-8")
    print("OK: updated export SQUADVAULT_TEST_DB to bind WORK_DB (v2).")

if __name__ == "__main__":
    main()
