from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

NEEDLE = "scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh"
BULLET = f"- {NEEDLE} — Ops index ↔ prove_ci gate execution parity (v1)\n"

SECTION = (
    f"{BEGIN}\n"
    "## CI guardrails entrypoints (bounded)\n"
    "\n"
    "# NOTE:\n"
    "# - This section is enforced by scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh\n"
    "# - Only list gate/check entrypoints you intend to be validated as discoverable.\n"
    "# - Format: `- scripts/<path> — description`\n"
    "\n"
    f"{BULLET}"
    f"{END}\n"
)

def main() -> None:
    if not DOC.exists():
        raise SystemExit(f"ERROR: missing {DOC}")

    text = DOC.read_text(encoding="utf-8")

    if BEGIN not in text or END not in text:
        # Fail-closed: create bounded section at end of file.
        new_text = text.rstrip() + "\n\n" + SECTION
        DOC.write_text(new_text, encoding="utf-8")
        print("UPDATED: added bounded entrypoints section:", DOC)
        return

    # Extract bounded region
    pre, rest = text.split(BEGIN, 1)
    bounded, post = rest.split(END, 1)

    if NEEDLE in bounded:
        print("OK: discoverability bullet already present in bounded section")
        return

    # Insert bullet just before END marker, preserving bounded content.
    bounded_stripped = bounded.rstrip() + "\n"
    if not bounded_stripped.endswith("\n"):
        bounded_stripped += "\n"

    # Ensure there's a newline separation before inserting
    if not bounded_stripped.endswith("\n"):
        bounded_stripped += "\n"

    new_bounded = bounded_stripped + BULLET
    new_text = pre + BEGIN + new_bounded + END + post
    DOC.write_text(new_text, encoding="utf-8")
    print("UPDATED: added discoverability bullet:", DOC)

if __name__ == "__main__":
    main()
