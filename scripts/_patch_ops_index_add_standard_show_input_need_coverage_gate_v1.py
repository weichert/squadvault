from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

LINE = "- scripts/gate_standard_show_input_need_coverage_v1.sh — Enforce deterministic InputNeed coverage baseline for STANDARD_SHOW_V1 (v1)\n"

def main() -> None:
    text = DOC.read_text(encoding="utf-8")

    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: expected bounded markers not found; refusing to patch.")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    if LINE.strip() in mid:
        print("OK: entry already present in bounded section.")
        return

    # Insert deterministically: append at end of bounded block (before END),
    # preserving a trailing newline.
    if not mid.endswith("\n"):
        mid += "\n"
    mid = mid + LINE

    DOC.write_text(pre + BEGIN + mid + END + post, encoding="utf-8")
    print("OK: inserted entry into SV_CI_GUARDRAILS_ENTRYPOINTS bounded section.")

if __name__ == "__main__":
    main()
