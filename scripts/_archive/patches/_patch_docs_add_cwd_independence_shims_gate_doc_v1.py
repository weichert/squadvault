from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
DOC   = Path("docs/80_indices/ops/CI_CWD_Independence_Shims_Gate_v1.0.md")

HEADER = "[SV_CANONICAL_HEADER_V1]\n"


def _doc_body() -> str:
    lines: list[str] = []
    lines.append(HEADER.rstrip("\n"))
    lines += [
        "Contract Name: CI CWD Independence Gate (Shims)",
        "Version: v1.0",
        "Status: CANONICAL",
        "",
        "Defers To:",
        "  - Canonical Operating Constitution (Tier 0)",
        "  - CI Guardrails Index (Tier 1)",
        "",
        "Default: Any behavior not explicitly permitted by this contract is forbidden.",
        "",
        "—",
        "",
        "## Purpose",
        "",
        "Ensure scripts that rely on repo-local shims (notably `./scripts/py`) are **CWD-independent**.",
        "In other words: the guardrails and proof suite must work even when invoked from a directory",
        "other than repo root.",
        "",
        "This prevents subtle breakage when tools run scripts via absolute paths, CI runners change CWD,",
        "or developers call scripts from nested directories.",
        "",
        "## Enforced By",
        "",
        "- Gate script: `scripts/gate_cwd_independence_shims_v1.sh`",
        "- CI runner: `scripts/prove_ci.sh`",
        "",
        "## Definition",
        "",
        "A script is CWD-independent if it:",
        "- Resolves repo root deterministically, and",
        "- Invokes repo-local shims via a stable path (e.g., `./scripts/py` from repo root, or absolute path).",
        "",
        "## Notes",
        "",
        "- This is a **runtime-enforced guardrail** (not advisory).",
        "- If a future script needs repo root, it must discover it (e.g., by walking parents to `.git`).",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing index: {INDEX}")

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(_doc_body(), encoding="utf-8")

    txt = INDEX.read_text(encoding="utf-8")

    link = "- [CI CWD Independence Gate (Shims) (v1.0)](CI_CWD_Independence_Shims_Gate_v1.0.md)\n"

    if link in txt:
        return

    section = "## CWD Independence\n"
    if section not in txt:
        # Prefer inserting near other CI guardrails sections; otherwise append.
        if not txt.endswith("\n"):
            txt += "\n"
        txt += "\n" + section

    before, after = txt.split(section, 1)
    if not after.startswith("\n"):
        after = "\n" + after
    txt = before + section + link + after

    INDEX.write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
