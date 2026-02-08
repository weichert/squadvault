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


def desired_block(existing_mid_lines: list[str]) -> str:
    # Canonical formatting MUST MATCH the committed registry formatting:
    # BEGIN
    # <blank line>
    # entries...
    # <blank line>
    # END
    uniq: dict[str, str] = {}

    for ln in existing_mid_lines:
        n = norm(ln)
        if not n:
            continue
        uniq[n] = ln.strip()

    for w in WANT:
        uniq[norm(w)] = w

    sorted_lines = sorted(uniq.values(), key=lambda x: x.split()[0])

    out: list[str] = []
    out.append(BEGIN)
    out.append("")  # blank line after BEGIN (canonical)
    out.extend(sorted_lines)
    out.append("")  # blank line before END (canonical)
    out.append(END)
    return "\\n".join(out)


def main() -> None:
    if not REG.exists():
        raise SystemExit(f"ERROR: missing {REG}")

    text = REG.read_text(encoding="utf-8")

    if BEGIN in text and END in text:
        pre, rest = text.split(BEGIN, 1)
        mid, post = rest.split(END, 1)

        # Reconstruct the *current* bounded block exactly as stored (including internal blanks).
        current_block = BEGIN + mid + END
        # mid currently begins with whatever immediately followed BEGIN in file;
        # splitlines keeps formatting stable for comparison.
        existing_mid_lines = mid.splitlines()

        want = desired_block(existing_mid_lines)

        # No-op if already byte-identical (format-stable)
        if current_block.strip("\\n") == want:
            return

        # Replace bounded region with desired formatting, preserve post EXACTLY (no lstrip).
        # Ensure we keep the original newline situation around the block by:
        # - leaving `pre` as-is
        # - writing `want` + whatever `post` had
        new_text = pre + want + post
        REG.write_text(new_text, encoding="utf-8")
        return

    # Block absent: append with a single separating newline.
    if not text.endswith("\\n"):
        text += "\\n"
    want = desired_block([])
    REG.write_text(text + "\\n" + want + "\\n", encoding="utf-8")


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
