from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

LINES = [
    "- scripts/gate_no_test_dir_case_drift_v1.sh — Enforce no test dir case drift (Tests/ vs tests/) (v1)\n",
    "- scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh — Proof: CI run does not mutate fixtures/ci_squadvault.sqlite (v1)\n",
]

def main() -> None:
    text = DOC.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: expected bounded markers not found; refusing to patch.")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    if not mid.endswith("\n"):
        mid += "\n"

    changed = False
    for line in LINES:
        if line.strip() in mid:
            continue
        mid += line
        changed = True

    if not changed:
        print("OK: entries already present in bounded section.")
        return

    DOC.write_text(pre + BEGIN + mid + END + post, encoding="utf-8")
    print("OK: inserted best-in-class guardrails into SV_CI_GUARDRAILS_ENTRYPOINTS bounded section.")

if __name__ == "__main__":
    main()
