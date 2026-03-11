from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/ops_orchestrate.sh")

BAD = """\
  die "idempotency failure: pass2 changed the diff state vs pass1"
  fi
fi
echo "==> idempotency OK (pass2 introduced no new changes)"
"""

GOOD = """\
  die "idempotency failure: pass2 changed the diff state vs pass1"
fi
echo "==> idempotency OK (pass2 introduced no new changes)"
"""


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if GOOD in s:
        print("OK: ops_orchestrate extra-fi fix already applied (v1).")
        return

    if BAD not in s:
        lines = s.splitlines()
        lo = max(0, 151 - 25)
        hi = min(len(lines), 151 + 25)
        excerpt = "\n".join(f"{i+1:4d}  {lines[i]}" for i in range(lo, hi))
        raise SystemExit(
            "ERROR: could not locate expected extra-fi block to patch (v1).\n"
            "---- excerpt around ~line 151 ----\n"
            f"{excerpt}\n"
            "---- end excerpt ----"
        )

    TARGET.write_text(s.replace(BAD, GOOD), encoding="utf-8")
    print("OK: patched ops_orchestrate (removed stray fi) (v1).")


if __name__ == "__main__":
    main()
