from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_rivalry_chronicle_end_to_end_v1.sh")

NEEDLE = '# Enforce Rivalry Chronicle output contract (v1): header + required metadata keys.'
ART_VAL_LINE = 'artifact_type_val = "RIVALRY_CHRONICLE_V1"'
UPSERT_LINE = 'meta = upsert(meta, "Artifact Type", artifact_type_val)'

def main() -> None:
    txt0 = PROVE.read_text(encoding="utf-8")

    if NEEDLE not in txt0:
        raise SystemExit("Refusing: expected v7+ contract block marker not found; cannot apply v9 safely.")

    # Idempotence
    if ART_VAL_LINE in txt0 and UPSERT_LINE in txt0:
        return

    lines = txt0.splitlines(True)

    inserted_val = False
    inserted_upsert = False
    out: list[str] = []

    for ln in lines:
        out.append(ln)

        # Insert artifact_type_val after state_val if present; else after week_val.
        if (not inserted_val) and ln.strip().startswith('state_val = '):
            out.append('artifact_type_val = "RIVALRY_CHRONICLE_V1"\n')
            inserted_val = True
        if (not inserted_val) and (not 'state_val = ' in txt0) and ln.strip().startswith('week_val = '):
            out.append('artifact_type_val = "RIVALRY_CHRONICLE_V1"\n')
            inserted_val = True

        # Insert upsert after State upsert if present; else after Week upsert.
        if (not inserted_upsert) and 'meta = upsert(meta, "State", state_val)' in ln:
            out.append('meta = upsert(meta, "Artifact Type", artifact_type_val)\n')
            inserted_upsert = True
        if (not inserted_upsert) and (not 'meta = upsert(meta, "State", state_val)' in txt0) and 'meta = upsert(meta, "Week", week_val)' in ln:
            out.append('meta = upsert(meta, "Artifact Type", artifact_type_val)\n')
            inserted_upsert = True

    txt1 = "".join(out)

    if not inserted_val:
        raise SystemExit("Refusing: could not insert artifact_type_val (expected state_val or week_val anchor).")
    if not inserted_upsert:
        raise SystemExit("Refusing: could not insert Artifact Type upsert (expected State or Week upsert anchor).")

    if txt1 != txt0:
        PROVE.write_text(txt1, encoding="utf-8")

if __name__ == "__main__":
    main()
