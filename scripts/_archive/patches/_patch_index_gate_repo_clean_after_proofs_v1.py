from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "80_indices" / "ops" / "CI_Guardrails_Index_v1.0.md"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

NEW_LINE = "- scripts/gate_repo_clean_after_proofs_v1.sh — Enforce repo clean after proofs (v1)\n"

def main() -> None:
  if not DOC.exists():
    raise SystemExit(f"ERROR: missing {DOC}")

  txt = DOC.read_text(encoding="utf-8")
  if BEGIN not in txt or END not in txt:
    raise SystemExit("ERROR: missing bounded ops entrypoints markers; refusing to patch.")

  pre, rest = txt.split(BEGIN, 1)
  mid, post = rest.split(END, 1)

  if NEW_LINE.strip() in mid:
    print("OK: ops entrypoints already include gate_repo_clean_after_proofs_v1 (noop)")
    return

  lines = mid.splitlines(keepends=True)
  bullets = [ln for ln in lines if ln.startswith("- scripts/")]

  bullets.append(NEW_LINE)
  bullets_sorted = sorted(set(bullets))

  rebuilt: list[str] = []
  for ln in lines:
    if ln.startswith("- scripts/"):
      continue
    rebuilt.append(ln)

  if rebuilt and not rebuilt[-1].endswith("\n"):
    rebuilt[-1] += "\n"
  rebuilt.extend(bullets_sorted)

  mid2 = "".join(rebuilt)
  DOC.write_text(pre + BEGIN + mid2 + END + post, encoding="utf-8")
  print("OK: indexed gate_repo_clean_after_proofs_v1 in ops entrypoints (v1)")

if __name__ == "__main__":
  main()
