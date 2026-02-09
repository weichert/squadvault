from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_contract_surface_completeness_v1.sh")

OLD = 'trap \'rm -rf "$tmpdir"\' EXIT'
NEW = 'trap \'[[ -n "${tmpdir:-}" ]] && rm -rf "$tmpdir"\' EXIT'

def norm(s: str) -> str:
    return s.replace("\r\n", "\n")

def main() -> None:
    s = norm(GATE.read_text(encoding="utf-8"))

    if NEW in s:
        print("OK: trap already safe (idempotent).")
        return

    if OLD not in s:
        raise SystemExit(
            "ERROR: expected tmpdir trap line not found.\n"
            "HINT: search for: trap 'rm -rf \"$tmpdir\"' EXIT"
        )

    s2 = s.replace(OLD, NEW, 1)
    GATE.write_text(s2, encoding="utf-8")
    print("OK: patched tmpdir cleanup trap to be set -u safe.")

if __name__ == "__main__":
    main()
