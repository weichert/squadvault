from __future__ import annotations

from pathlib import Path


PROVE_CI = Path("scripts/prove_ci.sh")


def _fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def main() -> None:
    if not PROVE_CI.exists():
        _fail(f"missing {PROVE_CI}")

    lines = PROVE_CI.read_text(encoding="utf-8").splitlines(True)

    target = '="${WORK_DB}"\n'
    idxs = [i for i, line in enumerate(lines) if line == target]

    if not idxs:
        _fail('expected to find stray line exactly \'"${WORK_DB}"\' (as \'"${WORK_DB}"\\n\'); not found')
    if len(idxs) != 1:
        _fail(f"expected exactly 1 stray line {target!r}, found {len(idxs)}")

    # Safety: ensure this line is near the export line (within next 10 lines)
    export_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "export SQUADVAULT_TEST_DB":
            export_idx = i
            break
    if export_idx is None:
        _fail("could not find 'export SQUADVAULT_TEST_DB' (refuse-to-guess)")

    if not (export_idx < idxs[0] <= export_idx + 10):
        _fail(f"stray line found at {idxs[0]+1}, not within 10 lines after export at {export_idx+1}; refuse-to-guess")

    del lines[idxs[0]]
    PROVE_CI.write_text("".join(lines), encoding="utf-8")
    print("OK: removed stray SQUADVAULT_TEST_DB rhs line (v3)")


if __name__ == "__main__":
    main()
