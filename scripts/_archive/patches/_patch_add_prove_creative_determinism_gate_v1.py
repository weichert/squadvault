from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN = "# SV_GATE: prove_creative_determinism (v1) begin"
END = "# SV_GATE: prove_creative_determinism (v1) end"

BLOCK = f"""\
{BEGIN}
echo "==> Prove: creative determinism (v1)"
bash scripts/prove_creative_determinism_v1.sh
{END}
"""

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"Missing {PROVE}")

    txt = PROVE.read_text(encoding="utf-8")

    if BEGIN in txt or END in txt:
        # Idempotent: if block already present, do nothing.
        return

    # Anchor strategy: insert near the end, before final success line if present.
    # We refuse if we can't find a stable insertion point that won't be ambiguous.
    candidates = [
        'echo "OK"',
        'echo "OK."',
        'echo "All OK"',
        'echo "All checks passed"',
    ]

    insert_at = -1
    found = None
    for c in candidates:
        idx = txt.rfind(c)
        if idx != -1:
            insert_at = idx
            found = c
            break

    if insert_at == -1:
        # fallback: append at end, but only if file ends with newline and contains "prove" header
        if "prove_ci" not in txt and "CI" not in txt:
            raise SystemExit("Refusing: scripts/prove_ci.sh shape unexpected (no known anchors).")
        if not txt.endswith("\n"):
            raise SystemExit("Refusing: scripts/prove_ci.sh missing trailing newline.")
        txt2 = txt + "\n" + BLOCK
        PROVE.write_text(txt2, encoding="utf-8")
        return

    # Insert BLOCK immediately before the found anchor line.
    before = txt[:insert_at]
    after = txt[insert_at:]
    if not before.endswith("\n"):
        # keep formatting sane
        before += "\n"
    txt2 = before + BLOCK + "\n" + after
    PROVE.write_text(txt2, encoding="utf-8")

if __name__ == "__main__":
    main()
