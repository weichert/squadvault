from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent

# v1 LOCK: canonical roots allowlist (frozen at patch time)
CANONICAL_ROOTS_V1 = ['docs/30_contract_cards', 'docs/40_specs', 'docs/80_indices', 'docs/canon_pointers', 'docs/canonical']

# v1 LOCK: canonical header marker
CANON_HEADER = '[SV_CANONICAL_HEADER_V1]'

# v1 LOCK: documentation maps (text only)
DOC_MAPS_V1 = ['docs/canonical/Documentation_Map_and_Canonical_References.md', 'docs/80_indices/signal_scout/Documentation_Map_Tier2_Addition_v1.4.md']

VERSIONED_RE = re.compile(r"_v\d+\.\d+", re.IGNORECASE)
MD_LINK_RE = re.compile(r"\]\(([^)]+)\)")
PATH_TOKEN_RE = re.compile(r"(docs/[A-Za-z0-9_\-./]+|scripts/[A-Za-z0-9_\-./]+)")

def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)

def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except Exception:
        return str(p)

def sorted_files_under(rel_root: str) -> List[Path]:
    root = REPO_ROOT / rel_root
    if not root.exists():
        die(f"FAIL: canonical root missing: {rel_root}")

    import os
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames.sort()
        filenames.sort()
        for fn in filenames:
            out.append(Path(dirpath) / fn)

    return out


def is_versioned_text_doc(p: Path) -> bool:
    if not VERSIONED_RE.search(p.name):
        return False
    return p.suffix.lower() in [".md", ".txt"]

def is_canonical_looking(p: Path, txt: str) -> bool:
    # Canonical-looking if versioned OR contains canonical header marker.
    if VERSIONED_RE.search(p.name):
        return True
    if CANON_HEADER in txt:
        return True
    return False

def gate_header_presence(files: List[Path]) -> None:
    missing: List[str] = []
    for p in files:
        # docs_integrity_scope_canonical_only_v1: header enforcement only applies to docs/canonical/**
        rp = rel(p)
        if not rp.startswith('docs/canonical/'):
            continue
        if not is_versioned_text_doc(p):
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        if CANON_HEADER not in txt:
            missing.append(rel(p))
    if missing:
        die("FAIL: versioned canonical artifacts missing canonical header marker:\n" + "\n".join(sorted(missing)))

def gate_duplicate_basenames(files: List[Path]) -> None:
    seen: Dict[str, str] = {}
    dups: List[str] = []
    for p in files:
        # Only consider canonical-looking artifacts to reduce false positives.
        if p.suffix.lower() not in [".md", ".txt"]:
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        if not is_canonical_looking(p, txt):
            continue
        base = p.name
        r = rel(p)
        if base in seen:
            dups.append(f"{base}:\n  - {seen[base]}\n  - {r}")
        else:
            seen[base] = r
    if dups:
        die("FAIL: duplicate canonical basenames detected (case-sensitive):\n" + "\n\n".join(sorted(dups)))

def extract_doc_map_refs(doc_map_paths: List[Path]) -> Set[str]:
    refs: Set[str] = set()
    for p in doc_map_paths:
        txt = p.read_text(encoding="utf-8", errors="replace")
        for m in MD_LINK_RE.findall(txt):
            t = m.strip()
            if t.startswith("http://") or t.startswith("https://") or t.startswith("#"):
                continue
            if t.startswith("./"):
                t = t[2:]
            if t.startswith("/"):
                t = t[1:]
            refs.add(t)
        for m in PATH_TOKEN_RE.findall(txt):
            t = m.strip()
            if t.startswith("/"):
                t = t[1:]
            refs.add(t)
    return set(sorted(refs))

def gate_doc_map_refs_exist(refs: Set[str]) -> None:
    missing: List[str] = []
    for r in sorted(refs):
        if not (r.startswith("docs/") or r.startswith("scripts/")):
            continue
        if not (REPO_ROOT / r).exists():
            missing.append(r)
    if missing:
        die("FAIL: documentation map references missing paths:\n" + "\n".join(missing))

def gate_ci_index_coverage(ci_index: Path) -> None:
    txt = ci_index.read_text(encoding="utf-8", errors="replace")
    # Minimal + explicit: index must reference invariant and the new runner name
    inv = "docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md"
    runner = "scripts/prove_docs_integrity_v1.sh"
    missing: List[str] = []
    if inv not in txt:
        missing.append(f"missing ref/link to invariant doc: {inv}")
    if runner not in txt:
        missing.append(f"missing ref/link to proof runner: {runner}")
    if missing:
        die("FAIL: CI guardrails index coverage gate failed:\n- " + "\n- ".join(missing))

def main() -> None:
    # Validate doc maps exist (fail-closed)
    doc_maps: List[Path] = []
    for s in DOC_MAPS_V1:
        p = REPO_ROOT / s
        if not p.exists():
            die(f"FAIL: required documentation map missing (v1): {s}")
        doc_maps.append(p)

    canon_files: List[Path] = []
    for rel_root in CANONICAL_ROOTS_V1:
        canon_files.extend(sorted_files_under(rel_root))

    gate_header_presence(canon_files)
    gate_duplicate_basenames(canon_files)

    refs = extract_doc_map_refs(doc_maps)
    gate_doc_map_refs_exist(refs)

    ci_index = REPO_ROOT / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
    if not ci_index.exists():
        die("FAIL: CI guardrails index missing: docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
    gate_ci_index_coverage(ci_index)

if __name__ == "__main__":
    main()
