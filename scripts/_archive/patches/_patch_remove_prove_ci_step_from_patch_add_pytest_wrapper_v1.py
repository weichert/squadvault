from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/patch_add_pytest_to_requirements_v1.sh")

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    # Remove the block that runs prove_ci.sh (it requires a clean repo).
    old = (
        'echo "==> prove_ci (local)"\n'
        'bash scripts/prove_ci.sh\n'
        '\n'
    )

    if old not in txt:
        raise SystemExit("ERROR: could not locate prove_ci block (refusing to guess)")

    out = txt.replace(old, "")
    TARGET.write_text(out, encoding="utf-8")
    print(f"OK: patched {TARGET}")

if __name__ == "__main__":
    main()
