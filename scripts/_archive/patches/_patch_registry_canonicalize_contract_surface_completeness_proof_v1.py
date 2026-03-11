from __future__ import annotations

from pathlib import Path

DOC = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

LINE = "- scripts/prove_contract_surface_completeness_v1.sh — Proof: contract surface completeness gate (v1)\n"


def refuse(msg: str) -> None:
  raise SystemExit(f"ERROR: {msg}")


def main() -> None:
  if not DOC.exists():
    refuse(f"missing {DOC}")

  s = DOC.read_text(encoding="utf-8")

  # If already present anywhere, no-op.
  if LINE.strip("\n") in s.splitlines():
    return

  lines = s.splitlines(True)

  # Deterministic insertion: after the first normal proof bullet line
  # (parser-friendly; avoids custom bounded blocks).
  insert_at = None
  for i, ln in enumerate(lines):
    if ln.startswith("- scripts/prove_") and ln.rstrip("\n").endswith(")"):
      # looks like canonical "— ... (vX)" formatting
      insert_at = i + 1
      break
    if ln.startswith("- scripts/prove_"):
      insert_at = i + 1
      break

  if insert_at is None:
    # fallback: after first "- scripts/" bullet
    for i, ln in enumerate(lines):
      if ln.startswith("- scripts/"):
        insert_at = i + 1
        break

  if insert_at is None:
    # last resort: append
    if not s.endswith("\n"):
      s += "\n"
    DOC.write_text(s + LINE, encoding="utf-8")
    return

  out: list[str] = []
  out.extend(lines[:insert_at])
  out.append(LINE)
  out.extend(lines[insert_at:])
  DOC.write_text("".join(out), encoding="utf-8")


if __name__ == "__main__":
  main()
