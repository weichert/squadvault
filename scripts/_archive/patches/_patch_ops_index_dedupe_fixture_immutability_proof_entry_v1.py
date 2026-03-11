from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

OLD = "- scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh — Proof: pytest does not mutate fixtures/ci_squadvault.sqlite (v1)\n"
KEEP = "- scripts/prove_pytest_does_not_dirty_fixture_db_v1.sh — Proof: CI run does not mutate fixtures/ci_squadvault.sqlite (v1)\n"

def main() -> None:
    text = DOC.read_text(encoding="utf-8")
    if BEGIN not in text or END not in text:
        raise SystemExit("ERROR: expected bounded markers not found; refusing to patch.")

    pre, rest = text.split(BEGIN, 1)
    mid, post = rest.split(END, 1)

    lines = mid.splitlines(keepends=True)

    out: list[str] = []
    removed = 0
    kept_present = False

    for ln in lines:
        if ln == OLD:
            removed += 1
            continue
        if ln == KEEP:
            kept_present = True
        out.append(ln)

    if not kept_present:
        # Ensure we keep the correct entry (append near end of bounded section).
        if len(out) > 0 and not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.append(KEEP)

    DOC.write_text(pre + BEGIN + "".join(out) + END + post, encoding="utf-8")
    print(f"OK: removed_old={removed} keep_present={kept_present}")

if __name__ == "__main__":
    main()
