from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/gate_enforce_test_db_routing_v1.sh")

ANCHOR = "set -euo pipefail\n"
BANNER = 'echo "=== Gate: Enforce canonical test DB routing (v1) ==="\n'
OK_LINE = 'echo "OK: test DB routing gate passed."\n'


def _fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def main() -> None:
    if not TARGET.exists():
        _fail(f"missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if ANCHOR not in s:
        _fail(f"anchor not found: {ANCHOR!r}")

    # Insert banner immediately after set -euo pipefail (idempotent)
    if BANNER not in s:
        s = s.replace(ANCHOR, ANCHOR + "\n" + BANNER, 1)

    # Add OK line at end (idempotent). Must remain after the failure block.
    if OK_LINE not in s:
        # Refuse-to-guess: only append if file ends with a newline
        if not s.endswith("\n"):
            _fail("gate script does not end with newline; refuse-to-guess")
        s = s + "\n" + OK_LINE

    TARGET.write_text(s, encoding="utf-8")
    print("OK: updated gate_enforce_test_db_routing_v1.sh to print banner + OK line")


if __name__ == "__main__":
    main()
