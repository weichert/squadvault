from __future__ import annotations

from pathlib import Path

F = Path("scripts/prove_golden_path.sh")

def main() -> None:
    if not F.exists():
        raise SystemExit(f"Missing {F}")

    lines = F.read_text(encoding="utf-8").splitlines(keepends=True)

    out = []
    changed = False
    for ln in lines:
        s = ln.strip()

        # Remove any leftover ROOT assignment line (defensive)
        if s.startswith("ROOT=") and "rev-parse" in s:
            changed = True
            continue

        # Remove any cd "$ROOT" (or cd "${ROOT}") usage
        if s in ('cd "$ROOT"', "cd '${ROOT}'", 'cd "${ROOT}"', "cd $ROOT"):
            changed = True
            continue

        out.append(ln)

    if not changed:
        return

    F.write_text("".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
