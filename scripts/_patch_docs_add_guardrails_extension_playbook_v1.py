from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
DOC   = Path("docs/80_indices/ops/CI_Guardrails_Extension_Playbook_v1.0.md")

HEADER = "[SV_CANONICAL_HEADER_V1]\n"


def _doc_body() -> str:
    lines: list[str] = []
    lines.append(HEADER.rstrip("\n"))
    lines += [
        "Contract Name: CI Guardrails Extension Playbook",
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
        "Provide a repeatable, low-risk workflow for adding new CI guardrails so the system remains:",
        "- deterministic",
        "- discoverable",
        "- enforceable",
        "- audited via patchers/wrappers",
        "",
        "## Rule of Thumb",
        "",
        "**If it’s in the CI Guardrails Index, it must be runtime-enforced.**",
        "If it’s only advice, it belongs elsewhere (or in a local-only helper).",
        "",
        "## Add a New CI Guardrail (Checklist)",
        "",
        "1) Implement the guardrail as a concrete script (gate) OR as a deterministic check inside an existing gate.",
        "   - Prefer a dedicated `scripts/gate_*.sh` when the behavior is distinct.",
        "",
        "2) Wire it into `scripts/prove_ci.sh` so CI actually runs it.",
        "",
        "3) Create a canonical doc under `docs/80_indices/ops/` describing:",
        "   - Purpose",
        "   - Enforced by (exact scripts)",
        "   - What constitutes pass/fail",
        "",
        "4) Add a link to the doc in `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`.",
        "",
        "5) Provide a versioned patcher+wrapper pair for all repo changes:",
        "   - `scripts/_patch_*.py` + `scripts/patch_*.sh`",
        "   - wrappers run via `./scripts/py` and include `bash -n` checks",
        "",
        "6) Verify from a clean repo:",
        "   - `./scripts/prove_ci.sh`",
        "",
        "7) Commit with a message that encodes scope + version (v1, v2…).",
        "",
        "## When Something Is Local-Only",
        "",
        "If the goal is workstation hygiene (shell init quirks, tool setup, etc.):",
        "- write a **local-only helper** under `scripts/prove_local_*.sh` (or similar),",
        "- link it in the CI Guardrails Index under a clearly labeled local-only section,",
        "- do NOT invoke it from `prove_ci.sh`.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    if not INDEX.exists():
        raise SystemExit(f"missing index: {INDEX}")

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(_doc_body(), encoding="utf-8")

    txt = INDEX.read_text(encoding="utf-8")
    link = "- [CI Guardrails Extension Playbook (v1.0)](CI_Guardrails_Extension_Playbook_v1.0.md)\n"

    if link in txt:
        return

    section = "## Guardrails Development\n"
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
