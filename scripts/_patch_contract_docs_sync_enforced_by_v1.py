from __future__ import annotations

from pathlib import Path

DOCS_DIR = Path("docs/contracts")
SCRIPTS_DIR = Path("scripts")


def die(msg: str) -> None:
  raise SystemExit(f"ERROR: {msg}")


def collect_contract_docs() -> list[Path]:
  if not DOCS_DIR.exists():
    return []
  docs = sorted(DOCS_DIR.glob("*_contract_*_v*.md"), key=lambda p: str(p))
  return [d for d in docs if d.is_file()]


def is_enforcement_surface(p: Path) -> bool:
  if p.parent != SCRIPTS_DIR:
    return False
  if p.suffix != ".sh":
    return False
  name = p.name
  return name.startswith("gate_") or name.startswith("prove_")


def reverse_scan_surfaces_for_doc(doc_rel: str) -> list[str]:
  needle = f"# SV_CONTRACT_DOC_PATH: {doc_rel}"
  found: list[str] = []
  for p in sorted(SCRIPTS_DIR.glob("*.sh"), key=lambda x: str(x)):
    if not is_enforcement_surface(p):
      continue
    lines = p.read_text(encoding="utf-8").splitlines()
    if needle in lines:
      if p.name.startswith("run_"):
        die(f"Forbidden: run_* script declares contract doc path marker: {p}")
      found.append(str(p))
  return sorted(set(found))


def build_enforced_by_block(surfaces: list[str]) -> str:
  lines = ["## Enforced By", ""]
  for sp in surfaces:
    lines.append(f"- `{sp}`")
  lines.append("")
  return "\n".join(lines)


def replace_or_insert_enforced_by(doc_text: str, new_block: str) -> str:
  lines = doc_text.splitlines(True)

  header_idx = None
  for i, line in enumerate(lines):
    if line.rstrip("\n") == "## Enforced By":
      header_idx = i
      break

  if header_idx is None:
    insert_at = 0
    for i, line in enumerate(lines):
      if line.startswith("# "):
        insert_at = i + 1
        break
    out = lines[:insert_at]
    if out and out[-1].strip() != "":
      out.append("\n")
    out.append(new_block)
    out.extend(lines[insert_at:])
    return "".join(out)

  end_idx = len(lines)
  for j in range(header_idx + 1, len(lines)):
    if lines[j].startswith("## "):
      end_idx = j
      break

  out = []
  out.extend(lines[:header_idx])
  if out and out[-1].strip() != "":
    out.append("\n")
  out.append(new_block)
  out.extend(lines[end_idx:])
  return "".join(out)


def main() -> None:
  docs = collect_contract_docs()
  if not docs:
    return

  if not SCRIPTS_DIR.exists():
    die("scripts/ directory missing")

  for doc in docs:
    doc_rel = str(doc)
    surfaces = reverse_scan_surfaces_for_doc(doc_rel)
    if not surfaces:
      die(f"No enforcement surfaces declare SV_CONTRACT_DOC_PATH for contract doc: {doc_rel}")

    new_block = build_enforced_by_block(surfaces)
    old = doc.read_text(encoding="utf-8")
    new = replace_or_insert_enforced_by(old, new_block)

    if new != old:
      doc.write_text(new, encoding="utf-8")


if __name__ == "__main__":
  main()
