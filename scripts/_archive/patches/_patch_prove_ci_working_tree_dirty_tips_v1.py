from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

NEEDLE = 'sv_clean="DIRTY"'

TIP_BLOCK = """\
  echo "TIP: A prior step dirtied the working tree. To see exactly what changed:"
  echo "TIP:   git status --porcelain=v1"
  echo "TIP:   git diff --name-only"
  echo "TIP: If this came from a patch wrapper, run the wrapper twice from clean to confirm idempotence."
  echo "TIP: Patchers must no-op when already canonical (avoid reordering blocks each run)."
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    text = TARGET.read_text(encoding="utf-8")
    if TIP_BLOCK in text:
        print("OK: working-tree dirty tips already present (v1 idempotent).")
        return

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inserted = False

    for line in lines:
        out.append(line)
        if (not inserted) and (NEEDLE in line):
            out.append(TIP_BLOCK)
            inserted = True

    if not inserted:
        raise SystemExit(f"ERROR: could not find needle in prove_ci.sh: {NEEDLE}")

    TARGET.write_text("".join(out), encoding="utf-8")
    print("OK: inserted working-tree dirty failure tips (v1).")

if __name__ == "__main__":
    main()
