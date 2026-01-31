from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "scripts" / "patch_writing_room_intake_exclusions_v1.sh"

def main() -> int:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    # We want:
    #   export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
    #   "$PY_BIN" -m pytest -q
    #
    # Replace the existing pytest line (whatever it is) in a conservative way.

    if "Step 3: run tests" not in s:
        raise SystemExit("ERROR: expected 'Step 3: run tests' echo not found; refusing to patch.")

    # Replace any line that invokes pytest in step 3 with the hardened form.
    lines = s.splitlines()
    out = []
    replaced = False

    for line in lines:
        if (not replaced) and ("pytest -q" in line):
            out.append('export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"')
            out.append('"$PY_BIN" -m pytest -q')
            replaced = True
        else:
            out.append(line)

    if not replaced:
        raise SystemExit("ERROR: did not find a 'pytest -q' invocation to replace; refusing to patch.")

    s2 = "\n".join(out) + "\n"
    TARGET.write_text(s2, encoding="utf-8")

    print(f"OK: patched {TARGET.relative_to(ROOT)}")
    print('Now runs tests with: export PYTHONPATH="$ROOT:$ROOT/src..." and "$PY_BIN" -m pytest -q')
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
