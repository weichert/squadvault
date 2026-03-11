from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

NEEDLE = '# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys.'
STATE_LINE = 'state_val = "APPROVED"'

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")

    if NEEDLE not in txt0:
        raise SystemExit("Refusing: expected v7 contract block marker not found; cannot apply v8 safely.")

    # Idempotence: if already contains state enforcement, no-op.
    if STATE_LINE in txt0 and 'meta = upsert(meta, "State", state_val)' in txt0:
        return

    lines = txt0.splitlines(True)

    # Locate the contract block start.
    start = None
    for i, ln in enumerate(lines):
        if NEEDLE in ln:
            start = i
            break
    if start is None:
        raise SystemExit("Refusing: could not locate contract block start line (unexpected).")

    # We will:
    # 1) Insert state_val immediately after week_val line (if present), else after season_val.
    # 2) Insert meta upsert for State after Week upsert line.
    out = []
    inserted_state_val = False
    inserted_state_upsert = False

    for i, ln in enumerate(lines):
        out.append(ln)

        # Insert state_val after week_val line.
        if (not inserted_state_val) and ln.strip().startswith('week_val = '):
            out.append('state_val = "APPROVED"\n')
            inserted_state_val = True

        # Fallback: if no week_val line existed for some reason, insert after season_val.
        if (not inserted_state_val) and ln.strip().startswith('season_val = '):
            # only do this if we haven't seen week_val by later; but we can't know yet.
            # We'll do a conservative insert here only if week_val is not in the file at all.
            pass

        # Insert meta upsert after Week upsert.
        if (not inserted_state_upsert) and 'meta = upsert(meta, "Week", week_val)' in ln:
            out.append('meta = upsert(meta, "State", state_val)\n')
            inserted_state_upsert = True

    txt1 = "".join(out)

    # If we didn't insert state_val (because week_val line wasn't found), do a safe one-time insert after season_val.
    if not inserted_state_val:
        if 'week_val = ' in txt1:
            raise SystemExit("Refusing: expected to insert state_val after week_val, but insertion did not occur.")
        # Insert after season_val if week_val truly absent (unexpected, but safe fallback).
        txt2_lines = txt1.splitlines(True)
        out2 = []
        done = False
        for ln in txt2_lines:
            out2.append(ln)
            if (not done) and ln.strip().startswith('season_val = '):
                out2.append('state_val = "APPROVED"\n')
                done = True
        txt1 = "".join(out2)
        inserted_state_val = True

    if not inserted_state_upsert:
        raise SystemExit('Refusing: could not locate Week upsert line to insert State upsert after.')

    if txt1 != txt0:
        PROVE.write_text(txt1, encoding="utf-8")

if __name__ == "__main__":
    main()
