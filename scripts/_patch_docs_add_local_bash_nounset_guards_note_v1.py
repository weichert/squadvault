from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
DOC = Path("docs/80_indices/ops/Local_Bash_Nounset_Guards_v1.0.md")

HEADER = "[SV_CANONICAL_HEADER_V1]\n"


def _doc_body() -> str:
    lines: list[str] = []
    lines.append(HEADER.rstrip("\n"))
    lines += [
        "Contract Name: Local Bash Nounset Guards",
        "Version: v1.0",
        "Status: CANONICAL",
        "",
        "Defers To:",
        "  - Canonical Operating Constitution (Tier 0)",
        "  - CI Guardrails Index (Tier 1) (informational linkage)",
        "",
        "Default: Any behavior not explicitly permitted by this contract is forbidden.",
        "",
        "—",
        "",
        "## Purpose",
        "",
        "Some environments/tools execute `bash` under `set -u` (nounset), often indirectly",
        "(e.g., wrappers, CI helpers, shell login/teardown hooks). In those contexts, a",
        "single unbound variable referenced by startup/teardown scripts can crash an",
        "otherwise-correct workflow.",
        "",
        "This note standardizes a minimal, explicit guard block for common variables that",
        "have been observed to fail under nounset.",
        "",
        "## Scope",
        "",
        "This is **local workstation hygiene**, not a repo runtime requirement:",
        "",
        "- Applies to: `~/.bashrc`, `~/.bash_profile` (and optionally `~/.profile` if used)",
        "- Does **not** modify repo behavior directly",
        "- Exists to prevent failures like: `-bash: <var>: unbound variable`",
        "",
        "## Canonical Guard Block",
        "",
        "Add exactly one block (dedupe prior ad-hoc lines) and keep it centralized:",
        "",
        "```bash",
        "# SV_NOUNSET_GUARDS_V1: guard common vars to avoid set -u startup/teardown failures",
        "# (Some shells/tools assume these exist; we run with set -u in many wrappers.)",
        ': "${HISTTIMEFORMAT:=}"',
        ': "${size:=}"',
        "```",
        "",
        "## Notes",
        "",
        "- Keep this block **single-source** (don’t scatter ad-hoc guards across files).",
        "- If you discover additional nounset failures, add them only after confirming the",
        "  variable is commonly assumed by your environment and that defaulting it is safe.",
        "",
        "## Verification",
        "",
        "```bash",
        "bash -lc 'set -u; : \"${HISTTIMEFORMAT?ok}\"; : \"${size?ok}\"; echo \"OK: guards survive set -u\"'",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing index: {INDEX}")

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(_doc_body(), encoding="utf-8")

    txt = INDEX.read_text(encoding="utf-8")
    link = "- [Local Bash Nounset Guards (v1.0)](Local_Bash_Nounset_Guards_v1.0.md)\n"

    if link in txt:
        return

    section = "## Local Workstation Hygiene\n"
    if section not in txt:
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
