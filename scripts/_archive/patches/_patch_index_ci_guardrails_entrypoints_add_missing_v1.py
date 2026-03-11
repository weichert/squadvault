from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

MISSING = [
    "- scripts/gate_cwd_independence_shims_v1.sh — CWD independence (shims) gate (v1)\n",
    "- scripts/gate_no_xtrace_v1.sh — No-xtrace guardrail gate (v1)\n",
]

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not DOC.exists():
        die(f"missing {DOC}")

    text = DOC.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        die("missing bounded markers for CI guardrails entrypoints section")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    lines = mid.splitlines(keepends=True)

    # Separate bullets from non-bullets within the bounded block
    bullets = [ln for ln in lines if ln.lstrip().startswith("- ")]
    nonbullets = [ln for ln in lines if not ln.lstrip().startswith("- ")]

    existing = set(ln.strip() for ln in bullets)
    for ln in MISSING:
        if ln.strip() not in existing:
            bullets.append(ln)

    # Canonicalize: sort bullets lexicographically (stable order)
    bullets = sorted(bullets)

    # Rebuild bounded block: keep non-bullets as-is, ensure blank line before bullets
    rebuilt: list[str] = []
    rebuilt.extend(nonbullets)

    if rebuilt and rebuilt[-1].strip() != "":
        rebuilt.append("\n")
    if not rebuilt:
        rebuilt.append("\n")

    rebuilt.extend(bullets)

    new_text = pre + BEGIN + "".join(rebuilt) + END + post
    if new_text != text:
        DOC.write_text(new_text, encoding="utf-8")

if __name__ == "__main__":
    main()
