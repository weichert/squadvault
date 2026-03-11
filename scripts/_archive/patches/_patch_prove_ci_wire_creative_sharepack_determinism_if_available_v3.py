from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

NEEDLE = 'echo "OK: CI proof suite passed"\n'
INSERT = (
    '\n'
    'echo "== Creative sharepack determinism (conditional) =="\\n'
    'bash scripts/prove_ci_creative_sharepack_if_available_v1.sh\\n'
    '\n'
)

def main() -> None:
    s = TARGET.read_text(encoding="utf-8")

    if "prove_ci_creative_sharepack_if_available_v1.sh" in s:
        print("OK: already wired (noop)")
        return

    if NEEDLE not in s:
        raise SystemExit(
            "ERROR: expected anchor not found in scripts/prove_ci.sh:\n"
            f"  {NEEDLE!r}\n"
            "Refusing to patch blindly."
        )

    out = s.replace(NEEDLE, NEEDLE + INSERT, 1)
    TARGET.write_text(out, encoding="utf-8", newline="\n")
    print("OK")

if __name__ == "__main__":
    main()
