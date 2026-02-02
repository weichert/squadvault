from __future__ import annotations

from pathlib import Path


PROVE_CI = Path("scripts/prove_ci.sh")

GATE_LINES = [
    "# Gate: enforce canonical test DB routing (v1)\n",
    "bash scripts/gate_enforce_test_db_routing_v1.sh\n",
]


def _fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def _strip_nl(s: str) -> str:
    return s[:-1] if s.endswith("\n") else s


def main() -> None:
    if not PROVE_CI.exists():
        _fail(f"missing {PROVE_CI}")

    lines = PROVE_CI.read_text(encoding="utf-8").splitlines(True)

    # 1) Repair the exact breakage that produced a line beginning with "=".
    #    This occurs when we split: `export SQUADVAULT_TEST_DB="$WORK_DB"` into:
    #      export SQUADVAULT_TEST_DB
    #      =/tmp/...
    #    or when a gate block got inserted between those two lines.
    repaired = False
    i = 0
    while i < len(lines) - 1:
        cur = _strip_nl(lines[i])
        nxt = _strip_nl(lines[i + 1])

        if cur == "export SQUADVAULT_TEST_DB" and (nxt.startswith("=$WORK_DB") or nxt.startswith("=/")):
            lines[i] = "export SQUADVAULT_TEST_DB" + nxt + "\n"
            del lines[i + 1]
            repaired = True
            break

        # If gate block sits between export and the stray "=..." line, remove the gate block then merge.
        if (
            cur == "export SQUADVAULT_TEST_DB"
            and i + 3 < len(lines)
            and lines[i + 1] == GATE_LINES[0]
            and lines[i + 2] == GATE_LINES[1]
            and (_strip_nl(lines[i + 3]).startswith("=$WORK_DB") or _strip_nl(lines[i + 3]).startswith("=/"))
        ):
            # Remove gate block
            del lines[i + 1 : i + 3]
            # Now merge export + "=..."
            nxt2 = _strip_nl(lines[i + 1])
            lines[i] = "export SQUADVAULT_TEST_DB" + nxt2 + "\n"
            del lines[i + 1]
            repaired = True
            break

        i += 1

    # 2) Locate the (now-correct) export line. We accept either:
    #    - export SQUADVAULT_TEST_DB
    #    - export SQUADVAULT_TEST_DB=...
    export_idx = None
    for j, line in enumerate(lines):
        s = _strip_nl(line).strip()
        if s == "export SQUADVAULT_TEST_DB" or s.startswith("export SQUADVAULT_TEST_DB="):
            export_idx = j
            break

    if export_idx is None:
        if repaired:
            _fail("repaired split export line, but still could not find 'export SQUADVAULT_TEST_DB' afterwards")
        _fail("could not find 'export SQUADVAULT_TEST_DB' in scripts/prove_ci.sh (refuse-to-guess)")

    # 3) Ensure gate appears immediately after the export line (as its own lines).
    #    If gate exists elsewhere, we leave it alone unless it is before export (which is suspicious).
    text = "".join(lines)
    gate_block = "".join(GATE_LINES)

    if gate_block in text:
        gate_pos = text.find(gate_block)
        export_pos = text.find(lines[export_idx])
        if gate_pos < export_pos:
            _fail("gate block exists but appears before SQUADVAULT_TEST_DB export; refuse-to-guess")
    else:
        # Insert after export line (with a blank line before for readability)
        insert = "\n" + gate_block
        lines.insert(export_idx + 1, insert)

    PROVE_CI.write_text("".join(lines), encoding="utf-8")
    print("OK: fixed prove_ci gate insertion (v2)")


if __name__ == "__main__":
    main()
