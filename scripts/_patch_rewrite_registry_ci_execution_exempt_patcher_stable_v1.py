from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/_patch_registry_add_ci_execution_exempt_locals_v1.py")

NEW = """from __future__ import annotations

from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

BEGIN = "<!-- SV_CI_EXECUTION_EXEMPT_v1_BEGIN -->"
END = "<!-- SV_CI_EXECUTION_EXEMPT_v1_END -->"

WANT = [
    "scripts/prove_local_clean_then_ci_v3.sh # local-only: developer workflow proof (not executed in CI)",
    "scripts/prove_local_shell_hygiene_v1.sh # local-only: interactive shell hygiene proof (not executed in CI)",
]


def norm(s: str) -> str:
    return " ".join(s.strip().split())


def canonical_block(lines: list[str]) -> str:
    # Canonical formatting: no blank lines inside block, sorted by path, stable trailing newline.
    uniq: dict[str, str] = {}
    for ln in lines:
        n = norm(ln)
        if not n:
            continue
        uniq[n] = ln.strip()

    # Ensure WANT present (idempotent)
    for w in WANT:
        uniq[norm(w)] = w

    sorted_lines = sorted(uniq.values(), key=lambda x: x.split()[0])

    out: list[str] = []
    out.append(BEGIN)
    out.extend(sorted_lines)
    out.append(END)
    return "\\n".join(out) + "\\n"


def main() -> None:
    if not REG.exists():
        raise SystemExit(f"ERROR: missing {REG}")

    text = REG.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        mid, post = rest.split(END, 1)

        existing = [ln.strip() for ln in mid.splitlines()]
        block = canonical_block(existing)

        # Replace entire bounded region with canonical block.
        # Preserve outside content; normalize to exactly one newline after END.
        new_text = pre + block + post.lstrip("\\n")
        REG.write_text(new_text, encoding="utf-8")
        return

    # If block absent, append canonical block with a single separating blank line.
    if not text.endswith("\\n"):
        text += "\\n"
    REG.write_text(text + "\\n" + canonical_block([]), encoding="utf-8")


if __name__ == "__main__":
    main()
"""


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing target patcher: {TARGET}")

    current = TARGET.read_text(encoding="utf-8")
    if current == NEW:
        return  # idempotent

    TARGET.write_text(NEW, encoding="utf-8")


if __name__ == "__main__":
    main()
