from __future__ import annotations

from pathlib import Path

TARGET = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

OLD = (
  "- `scripts/prove_local_clean_then_ci_v2.sh` — detects common untracked scratch "
  "patcher/wrapper files (dry-run by default; requires `SV_LOCAL_CLEAN=1` to delete) "
  "and then runs `bash scripts/prove_ci.sh`"
)

NEW = (
  "- `scripts/prove_local_clean_then_ci_v3.sh` — local-only helper: cleans *only* "
  "untracked scratch files named `scripts/_patch__*.py` and `scripts/patch__*.sh` "
  "(dry-run by default; requires `SV_LOCAL_CLEAN=1` to delete), then runs "
  "`bash scripts/prove_ci.sh`"
)


def main() -> None:
  if not TARGET.exists():
    raise SystemExit(f"missing target: {TARGET}")

  txt = TARGET.read_text(encoding="utf-8")

  if "prove_local_clean_then_ci_v3.sh" in txt:
    print("OK: index already points to v3")
    return

  if OLD not in txt:
    raise SystemExit(
      "Refusing to patch: expected v2 bullet not found (file changed unexpectedly)."
    )

  TARGET.write_text(txt.replace(OLD, NEW, 1), encoding="utf-8")
  print("OK: updated CI_Guardrails_Index to reference v3 local helper")


if __name__ == "__main__":
  main()
