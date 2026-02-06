from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/check_python_shim_compliance_v2.sh")
MARKER = "Python shim compliance gate (v2)"

def _refuse(msg: str) -> None:
    raise SystemExit(f"REFUSAL: {msg}")

def main() -> None:
    if not GATE.exists():
        _refuse(f"missing {GATE}")

    txt = GATE.read_text(encoding="utf-8")
    if MARKER not in txt:
        _refuse(f"unexpected gate contents (missing marker: {MARKER})")

    # We update common boundary snippets used in grep -E patterns.
    # Goal: treat ':' as a valid token boundary (grep -nH produces file:line:content).
    #
    # We *only* add ':' when it is absent (idempotent).
    replacements = [
        # group boundary: (^|[...])
        ("(^|[[:space:];&(])", "(^|[[:space:];&(:])"),
        ("(^|[[:space:];&(:])", "(^|[[:space:];&(:])"),  # already ok

        # class used in helper: ([...]) or direct [...]; we handle the common literal
        ("[[:space:];&(]", "[[:space:];&(:]"),
        ("[[:space:];&(:]", "[[:space:];&(:]"),  # already ok
    ]

    changed = False
    for a, b in replacements:
        if a in txt and a != b:
            txt2 = txt.replace(a, b)
            if txt2 != txt:
                txt = txt2
                changed = True

    # Also ensure we didn't accidentally create a weird duplicate like '&(:(]'
    # (cheap normalization pass)
    txt2 = txt.replace("[[:space:];&(:(:]", "[[:space:];&(:]")
    if txt2 != txt:
        txt = txt2
        changed = True

    if changed:
        GATE.write_text(txt, encoding="utf-8")

if __name__ == "__main__":
    main()
