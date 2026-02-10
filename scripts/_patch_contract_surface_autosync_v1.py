from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs" / "contracts"
SCRIPTS_DIR = REPO_ROOT / "scripts"

DOC_GLOB = "*_contract_*_v*.md"

ENFORCED_BY_HEADER_RE = re.compile(r"^##\s+Enforced By\s*$", re.IGNORECASE)
HEADING_RE = re.compile(r"^##\s+")
BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")

NAME_MARK_RE = re.compile(r"^#\s*SV_CONTRACT_NAME:\s*(.+?)\s*$")
DOC_MARK_RE = re.compile(r"^#\s*SV_CONTRACT_DOC_PATH:\s*(.+?)\s*$")

ENFORCEMENT_RE = re.compile(r"^scripts/(gate_.+\.sh|prove_.+\.sh)$")

H1_ENUM_RE = re.compile(r"^#\s+([A-Z0-9_]+)\s*$")
CONTRACT_NAME_FIELD_RE = re.compile(r"^(?:\*\*)?Contract Name(?:\*\*)?:\s*([A-Z0-9_]+)\s*$", re.IGNORECASE)


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="strict")


def _write_text_if_changed(p: Path, new_text: str) -> bool:
    old = _read_text(p)
    if old == new_text:
        return False
    p.write_text(new_text, encoding="utf-8", newline="\n")
    return True


def _expected_contract_name_from_doc(doc_path: Path) -> str:
    """
    Canonical contract name priority:
      1) "Contract Name: SOME_ENUM"
      2) H1 "# SOME_ENUM" (prefers ones containing CONTRACT)
      3) Fallback: UPPERCASE(doc filename stem)
         e.g. rivalry_chronicle_contract_output_v1.md -> RIVALRY_CHRONICLE_CONTRACT_OUTPUT_V1
    """
    text = _read_text(doc_path)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m_field = CONTRACT_NAME_FIELD_RE.match(line)
        if m_field:
            return m_field.group(1).strip()

        m_h1 = H1_ENUM_RE.match(line)
        if m_h1:
            candidate = m_h1.group(1).strip()
            if "CONTRACT" in candidate:
                return candidate

        if line.startswith("## "):
            break

    return doc_path.stem.upper()


def _extract_enforced_by_list(doc_text: str) -> List[str]:
    lines = doc_text.splitlines()
    out: List[str] = []
    in_block = False
    for line in lines:
        if ENFORCED_BY_HEADER_RE.match(line):
            in_block = True
            continue
        if in_block:
            if HEADING_RE.match(line):
                break
            m = BULLET_RE.match(line)
            if m:
                out.append(m.group(1).strip())
    norm: List[str] = []
    for x in out:
        x = x.strip()
        if not x:
            continue
        if x.startswith("./"):
            x = x[2:]
        norm.append(x)
    return norm


def _rewrite_enforced_by_section(doc_text: str, new_items: List[str]) -> str:
    lines = doc_text.splitlines()
    new_block: List[str] = ["## Enforced By", ""]
    for item in new_items:
        new_block.append(f"- {item}")
    new_block.append("")

    out: List[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        line = lines[i]
        if ENFORCED_BY_HEADER_RE.match(line):
            out.extend(new_block)
            i += 1
            while i < len(lines) and not HEADING_RE.match(lines[i]):
                i += 1
            replaced = True
            continue
        out.append(line)
        i += 1

    if not replaced:
        if out and out[-1].strip() != "":
            out.append("")
        out.extend(new_block)

    return "\n".join(out) + "\n"


def _scan_script_declares(script_text: str) -> List[Tuple[Optional[str], str]]:
    pairs: List[Tuple[Optional[str], str]] = []
    current_name: Optional[str] = None
    for line in script_text.splitlines():
        mn = NAME_MARK_RE.match(line)
        if mn:
            current_name = mn.group(1).strip()
            continue
        md = DOC_MARK_RE.match(line)
        if md:
            pairs.append((current_name, md.group(1).strip()))
            current_name = None
    return pairs


def _remove_all_contract_markers(script_text: str) -> str:
    out_lines: List[str] = []
    for line in script_text.splitlines():
        if NAME_MARK_RE.match(line) or DOC_MARK_RE.match(line):
            continue
        out_lines.append(line)
    return "\n".join(out_lines) + "\n"


def _ensure_markers_for_contract(script_text: str, expected_name: str, expected_doc_path: str) -> str:
    lines = script_text.splitlines()

    for idx, line in enumerate(lines):
        if NAME_MARK_RE.match(line):
            lines[idx] = f"# SV_CONTRACT_NAME: {expected_name}"
        elif DOC_MARK_RE.match(line):
            lines[idx] = f"# SV_CONTRACT_DOC_PATH: {expected_doc_path}"

    has_name = any(NAME_MARK_RE.match(l) for l in lines)
    has_doc = any(DOC_MARK_RE.match(l) for l in lines)
    if has_name and has_doc:
        return "\n".join(lines) + "\n"

    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
        if insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        if insert_at < len(lines) and lines[insert_at].strip() == "set -euo pipefail":
            insert_at += 1
            if insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1

    marker_block = [
        f"# SV_CONTRACT_NAME: {expected_name}",
        f"# SV_CONTRACT_DOC_PATH: {expected_doc_path}",
        "",
    ]
    lines = lines[:insert_at] + marker_block + lines[insert_at:]
    return "\n".join(lines) + "\n"


def main() -> int:
    contract_docs = sorted(DOCS_DIR.glob(DOC_GLOB), key=lambda p: str(p))

    doc_rel_to_name: Dict[str, str] = {}
    script_rel_to_docs: Dict[str, Set[str]] = {}

    for p in contract_docs:
        doc_rel = p.relative_to(REPO_ROOT).as_posix()
        doc_rel_to_name[doc_rel] = _expected_contract_name_from_doc(p)

        listed = _extract_enforced_by_list(_read_text(p))
        for item in listed:
            if item.startswith("./"):
                item = item[2:]
            if ENFORCEMENT_RE.match(item):
                script_rel_to_docs.setdefault(item, set()).add(doc_rel)

    script_paths = sorted(SCRIPTS_DIR.glob("*.sh"), key=lambda p: str(p))

    # 1) Remove markers from non-enforcement scripts
    for sp in script_paths:
        rel = sp.relative_to(REPO_ROOT).as_posix()
        is_enforcement = rel.startswith("scripts/gate_") or rel.startswith("scripts/prove_")
        text = _read_text(sp)
        if not is_enforcement and (NAME_MARK_RE.search(text) or DOC_MARK_RE.search(text)):
            _write_text_if_changed(sp, _remove_all_contract_markers(text))

    # 2) Reverse scan + repair
    declaring: Dict[str, Set[str]] = {doc_rel: set() for doc_rel in doc_rel_to_name.keys()}

    for sp in script_paths:
        rel = sp.relative_to(REPO_ROOT).as_posix()
        if not (rel.startswith("scripts/gate_") or rel.startswith("scripts/prove_")):
            continue

        text = _read_text(sp)
        new_text = text

        # Backfill markers if DOC_PATH missing but uniquely referenced by one doc
        if not DOC_MARK_RE.search(text):
            docs = script_rel_to_docs.get(rel, set())
            if len(docs) == 1:
                doc_rel = sorted(docs)[0]
                expected_name = doc_rel_to_name[doc_rel]
                declaring[doc_rel].add(rel)
                new_text = _ensure_markers_for_contract(new_text, expected_name, doc_rel)

        # Normal reverse-scan declarations
        for (found_name, found_doc) in _scan_script_declares(text):
            if found_doc.startswith("./"):
                found_doc = found_doc[2:]
            if found_doc in doc_rel_to_name:
                expected_name = doc_rel_to_name[found_doc]
                declaring[found_doc].add(rel)
                if found_name != expected_name:
                    new_text = _ensure_markers_for_contract(new_text, expected_name, found_doc)

        if new_text != text:
            _write_text_if_changed(sp, new_text)

    # 3) Forward scan: repair any listed enforcement scripts that exist
    for doc_path in contract_docs:
        doc_rel = doc_path.relative_to(REPO_ROOT).as_posix()
        expected_name = doc_rel_to_name[doc_rel]
        for item in _extract_enforced_by_list(_read_text(doc_path)):
            if item.startswith("./"):
                item = item[2:]
            if not ENFORCEMENT_RE.match(item):
                continue
            sp = REPO_ROOT / item
            if not sp.exists():
                continue
            st = _read_text(sp)
            repaired = _ensure_markers_for_contract(st, expected_name, doc_rel)
            if repaired != st:
                _write_text_if_changed(sp, repaired)

    # 4) Rewrite docs' Enforced By to EXACT declaring set
    for doc_path in contract_docs:
        doc_rel = doc_path.relative_to(REPO_ROOT).as_posix()
        items = sorted(declaring.get(doc_rel, set()), key=lambda s: s)
        items = [x for x in items if ENFORCEMENT_RE.match(x)]
        _write_text_if_changed(doc_path, _rewrite_enforced_by_section(_read_text(doc_path), items))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
