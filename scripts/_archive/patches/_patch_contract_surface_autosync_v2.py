from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
CONTRACTS_DIR = REPO_ROOT / "docs" / "contracts"

LC_ALL_C = os.environ.get("LC_ALL") == "C"


def die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def note(msg: str) -> None:
    print(msg)


def norm_lf(s: str) -> str:
    return s.replace("\n", "\n").replace("\n", "\n")


def stable_sorted(xs: Iterable[str]) -> List[str]:
    # Deterministic ordering (LC_ALL=C style: python sorts by codepoint deterministically)
    return sorted(set(xs))


def is_enforcement_script(path: Path) -> bool:
    if path.suffix != ".sh":
        return False
    n = path.name
    return n.startswith("gate_") or n.startswith("prove_")


def script_rel(p: Path) -> str:
    return str(p.relative_to(REPO_ROOT)).replace("\\", "/")


@dataclass(frozen=True)
class DeclLine:
    idx: int
    raw: str
    key: str  # "name" or "doc"
    value: str


# Accept common assignment shapes:
#   SV_CONTRACT_NAME="X"
#   export SV_CONTRACT_NAME='X'
#   SV_CONTRACT_DOC_PATH=docs/contracts/foo.md
#   export SV_CONTRACT_DOC_PATH="docs/contracts/foo.md"
NAME_RE = re.compile(
    r"""^(?P<prefix>\s*(?:export\s+)?)SV_CONTRACT_NAME\s*=\s*(?P<rhs>.+?)\s*$"""
)
DOC_RE = re.compile(
    r"""^(?P<prefix>\s*(?:export\s+)?)SV_CONTRACT_DOC_PATH\s*=\s*(?P<rhs>.+?)\s*$"""
)

# Simple RHS parser: strip quotes if present, strip trailing comments
TRAILING_COMMENT_RE = re.compile(r"\s+#.*$")


def parse_rhs_value(rhs: str) -> str:
    rhs = rhs.strip()
    rhs = TRAILING_COMMENT_RE.sub("", rhs).strip()
    if (rhs.startswith("'") and rhs.endswith("'")) or (rhs.startswith('"') and rhs.endswith('"')):
        rhs = rhs[1:-1]
    return rhs.strip()


def quote_like(original_rhs: str, new_value: str) -> str:
    o = original_rhs.strip()
    o2 = TRAILING_COMMENT_RE.sub("", o).strip()
    if o2.startswith("'") and o2.endswith("'"):
        return "'" + new_value.replace("'", "'\"'\"'") + "'"  # safe-ish in shell
    if o2.startswith('"') and o2.endswith('"'):
        # Keep it simple: escape embedded double quotes + backslashes
        v = new_value.replace("\\", "\\\\").replace('"', '\\"')
        return '"' + v + '"'
    # Unquoted originally: prefer quoted to be safe/deterministic.
    v = new_value.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + v + '"'


def read_text(p: Path) -> str:
    return norm_lf(p.read_text(encoding="utf-8"))


def write_text_if_changed(p: Path, new: str) -> bool:
    old = read_text(p)
    if old == new:
        return False
    p.write_text(new, encoding="utf-8")
    return True


def find_decl_lines(lines: List[str]) -> List[DeclLine]:
    out: List[DeclLine] = []
    for i, raw in enumerate(lines):
        m = NAME_RE.match(raw)
        if m:
            rhs = m.group("rhs")
            out.append(DeclLine(i, raw, "name", parse_rhs_value(rhs)))
            continue
        m = DOC_RE.match(raw)
        if m:
            rhs = m.group("rhs")
            out.append(DeclLine(i, raw, "doc", parse_rhs_value(rhs)))
            continue
    return out


@dataclass
class Pair:
    name_idx: Optional[int]
    doc_idx: Optional[int]
    doc_path: Optional[str]
    name: Optional[str]


def pair_decls(decls: List[DeclLine], window: int = 5) -> Tuple[List[Pair], List[int], List[int]]:
    """
    Pair NAME/DOC lines within a small adjacency window to prevent cross-pairing.
    Returns (pairs, unpaired_name_idxs, unpaired_doc_idxs).
    """
    name_idxs = [d.idx for d in decls if d.key == "name"]
    doc_idxs = [d.idx for d in decls if d.key == "doc"]

    # Greedy pairing anchored by DOC, then closest NAME within window.
    decl_by_idx = {d.idx: d for d in decls}

    used_names: Set[int] = set()
    used_docs: Set[int] = set()
    pairs: List[Pair] = []

    for di in doc_idxs:
        d = decl_by_idx[di]
        best: Optional[int] = None
        best_dist = 10**9
        for ni in name_idxs:
            if ni in used_names:
                continue
            dist = abs(ni - di)
            if dist == 0:
                continue
            if dist <= window and dist < best_dist:
                best = ni
                best_dist = dist
        if best is not None:
            used_docs.add(di)
            used_names.add(best)
            n = decl_by_idx[best]
            pairs.append(Pair(name_idx=best, doc_idx=di, doc_path=d.value, name=n.value))
        else:
            # DOC without a nearby NAME: still record a partial pair anchored by DOC.
            used_docs.add(di)
            pairs.append(Pair(name_idx=None, doc_idx=di, doc_path=d.value, name=None))

    unpaired_names = [ni for ni in name_idxs if ni not in used_names]
    unpaired_docs = [di for di in doc_idxs if di not in used_docs]
    return pairs, unpaired_names, unpaired_docs


CONTRACT_NAME_FIELD_RE = re.compile(r"^\s*\*\*Contract Name\*\*\s*:\s*(.+?)\s*$", re.IGNORECASE)
# Some docs may use "Contract Name" on its own line or similar patterns; keep conservative.
H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")


def doc_stem_upper(doc_path: Path) -> str:
    return doc_path.name.replace(".md", "").upper()


def expected_contract_name(doc_path: Path) -> str:
    """
    Expected contract name:
      - explicit "Contract Name:" field if present
      - else H1 enum if present (we treat as literal)
      - else DOC_STEM.upper()
    """
    txt = read_text(doc_path)
    for line in txt.split("\n"):
        m = CONTRACT_NAME_FIELD_RE.match(line)
        if m:
            return m.group(1).strip()
    for line in txt.split("\n"):
        m = H1_RE.match(line)
        if m:
            return m.group(1).strip()
    return doc_stem_upper(doc_path)


ENFORCED_BY_HEADER = "## Enforced By"


def split_enforced_by_section(md: str) -> Tuple[str, str, str, int]:
    """
    Returns (pre, section_body, post, count_headers_found).
    section_body excludes the header line; it is the content until next H2 (## ) or EOF.
    If header not found: count=0 and section_body=""
    If multiple found: returns first split; caller will canonicalize by removing all and inserting one.
    """
    lines = md.split("\n")
    header_idxs = [i for i, ln in enumerate(lines) if ln.strip() == ENFORCED_BY_HEADER]
    if not header_idxs:
        return md, "", "", 0

    first = header_idxs[0]

    # Find end at next H2 (## ...) after first (excluding the header itself)
    end = len(lines)
    for j in range(first + 1, len(lines)):
        if lines[j].startswith("## ") and lines[j].strip() != ENFORCED_BY_HEADER:
            end = j
            break

    pre = "\n".join(lines[: first + 1])  # includes header line
    body = "\n".join(lines[first + 1 : end])
    post = "\n".join(lines[end:])
    return pre, body, post, len(header_idxs)


BULLET_RE = re.compile(r"^\s*[-*]\s+(.*?)\s*$")


def parse_enforced_by_bullets(md: str) -> List[str]:
    pre, body, _post, count = split_enforced_by_section(md)
    if count == 0:
        return []
    out: List[str] = []
    for ln in body.split("\n"):
        m = BULLET_RE.match(ln)
        if m:
            out.append(m.group(1).strip())
    return out


def canonicalize_enforced_by(md: str, enforcement_paths: Sequence[str]) -> str:
    """
    Ensure exactly one Enforced By section with sorted unique bullets.
    Remove any non-enforcement entries (anything not scripts/gate_*.sh or scripts/prove_*.sh).
    """
    lines = md.split("\n")

    # Remove all existing Enforced By sections (if any)
    out: List[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == ENFORCED_BY_HEADER:
            # skip header + its content until next H2 or EOF
            i += 1
            while i < len(lines) and not (lines[i].startswith("## ") and lines[i].strip() != ENFORCED_BY_HEADER):
                i += 1
            continue
        out.append(lines[i])
        i += 1

    md_no_sections = "\n".join(out).rstrip("\n") + "\n"

    # Prepare canonical bullets (only enforcement scripts, must exist)
    cleaned: List[str] = []
    for p in stable_sorted(enforcement_paths):
        if not (p.startswith("scripts/gate_") or p.startswith("scripts/prove_")):
            continue
        if not (REPO_ROOT / p).exists():
            die(f"Doc canonicalization wants to reference missing enforcement script: {p}")
        cleaned.append(p)

    section = ENFORCED_BY_HEADER + "\n"
    for p in cleaned:
        section += f"- {p}\n"
    section += "\n"

    # Insert section:
    # Prefer: after first H1 line; otherwise at top.
    out2: List[str] = []
    inserted = False
    for ln in md_no_sections.split("\n"):
        out2.append(ln)
        if (not inserted) and ln.startswith("# "):
            out2.append("")  # blank line
            out2.append(section.rstrip("\n"))
            inserted = True
    if not inserted:
        out2 = [section.rstrip("\n")] + [""] + out2

    final = "\n".join(out2).rstrip("\n") + "\n"
    return final


def remove_markers_from_non_enforcement_scripts() -> List[str]:
    """
    Any scripts/*.sh not gate_*.sh or prove_*.sh must not contain SV_CONTRACT_NAME / SV_CONTRACT_DOC_PATH
    *assignment lines*. Remove only true marker assignment lines (NAME_RE/DOC_RE), not arbitrary mentions.
    Returns list of changed file paths (rel).
    """
    changed: List[str] = []
    for p in stable_sorted([str(x) for x in SCRIPTS_DIR.glob("*.sh")]):
        path = Path(p)
        if is_enforcement_script(path):
            continue

        txt = read_text(path)
        lines = txt.split("\n")
        new_lines: List[str] = []
        dirty = False
        for ln in lines:
            # Remove only actual marker assignment lines
            if NAME_RE.match(ln) or DOC_RE.match(ln):
                dirty = True
                continue
            new_lines.append(ln)

        new_txt = "\n".join(new_lines).rstrip("\n") + "\n"
        if dirty and write_text_if_changed(path, new_txt):
            changed.append(script_rel(path))
    return changed
def build_existing_doc_enforced_by_index() -> Dict[str, Set[str]]:
    """
    Read docs/contracts/*_contract_*_v*.md and build:
      enforcement_script -> set(doc_rel_paths)
    Used for inferring DOC_PATH for NAME-only cases.
    """
    idx: Dict[str, Set[str]] = {}
    if not CONTRACTS_DIR.exists():
        return idx
    for doc in sorted(CONTRACTS_DIR.glob("*_contract_*_v*.md")):
        md = read_text(doc)
        bullets = parse_enforced_by_bullets(md)
        for b in bullets:
            if b.startswith("scripts/gate_") or b.startswith("scripts/prove_"):
                idx.setdefault(b, set()).add(script_rel(doc))
    return idx


def load_contract_docs() -> List[Path]:
    if not CONTRACTS_DIR.exists():
        return []
    return sorted(CONTRACTS_DIR.glob("*_contract_*_v*.md"))


def normalize_doc_rel(doc_path_value: str) -> str:
    # Keep as forward-slash rel path if possible.
    s = doc_path_value.strip().replace("\\", "/")
    if s.startswith("./"):
        s = s[2:]
    return s


def ensure_doc_exists(doc_rel: str) -> Path:
    p = REPO_ROOT / doc_rel
    if not p.exists():
        die(f"SV_CONTRACT_DOC_PATH references missing doc: {doc_rel}")
    return p


def rewrite_script_with_pairs(
    script: Path,
    pairs: List[Pair],
    unpaired_names: List[int],
    unpaired_docs: List[int],
    doc_enforced_by_index: Dict[str, Set[str]],
) -> Tuple[bool, Dict[str, Set[str]]]:
    """
    Apply v2 rules:
      - Multi-contract support: treat each DOC independently.
      - Pairing hygiene: within window (already paired).
      - Mismatch counts:
          * DOC without NAME: insert NAME adjacent (above DOC) using expected name.
          * NAME without DOC: infer only if script appears in exactly one doc's Enforced By;
            otherwise deterministic error.
      - For each DOC: repair NAME to expected canonical contract name.
    Returns (changed?, per_doc_declares {doc_rel -> set(enforcement_script_rel)} derived from this script)
    """
    rel_script = script_rel(script)
    txt = read_text(script)
    lines = txt.split("\n")

    per_doc: Dict[str, Set[str]] = {}

    # Build quick lookup for decl rhs original text for quote preservation
    decls = find_decl_lines(lines)
    decl_by_idx = {d.idx: d for d in decls}

    changed = False

    # Handle DOC-anchored pairs (including DOC-only)
    # Sort by doc_idx to keep edits stable.
    for pair in sorted([p for p in pairs if p.doc_idx is not None], key=lambda p: int(p.doc_idx or 0)):
        assert pair.doc_idx is not None
        doc_rel = normalize_doc_rel(pair.doc_path or "")
        doc_abs = ensure_doc_exists(doc_rel)
        exp_name = expected_contract_name(doc_abs)

        per_doc.setdefault(doc_rel, set()).add(rel_script)

        if pair.name_idx is None:
            # Insert NAME line directly above DOC line (stable insertion).
            doc_line = lines[pair.doc_idx]
            m = DOC_RE.match(doc_line)
            if not m:
                continue
            prefix = m.group("prefix") or ""
            # Insert as exported if DOC was exported.
            export_prefix = prefix
            rhs = quote_like('"X"', exp_name)
            ins = f"{export_prefix}SV_CONTRACT_NAME={rhs}"
            lines.insert(pair.doc_idx, ins)
            changed = True
            # Adjust indices after insertion: simplest is to stop trying to keep indices perfectly; we only need stable output.
            # Update: also bump following doc_idx positions, but we won't reuse them further.
        else:
            # Rewrite NAME value if not expected.
            ni = pair.name_idx
            nline = lines[ni]
            m = NAME_RE.match(nline)
            if not m:
                continue
            d = decl_by_idx.get(ni)
            old_name = d.value if d else None
            if old_name != exp_name:
                rhs = quote_like(m.group("rhs"), exp_name)
                prefix = m.group("prefix") or ""
                lines[ni] = f"{prefix}SV_CONTRACT_NAME={rhs}"
                changed = True

    # Handle NAME-only leftovers (unpaired NAME)
    if unpaired_docs:
        # Should not happen with DOC-anchored greedy pairing, but if it does, error.
        offs = ", ".join(str(i + 1) for i in sorted(unpaired_docs))
        die(f"{rel_script}: Unpaired SV_CONTRACT_DOC_PATH lines at (1-indexed): {offs}")

    if unpaired_names:
        # Infer doc path only if uniquely referenced by exactly one contract doc’s Enforced By.
        candidates = doc_enforced_by_index.get(rel_script, set())
        if len(candidates) == 1:
            inferred_doc_rel = stable_sorted(candidates)[0]
            doc_abs = ensure_doc_exists(inferred_doc_rel)
            exp_name = expected_contract_name(doc_abs)

            # For each unpaired NAME, insert DOC_PATH line just below it.
            # Also repair NAME to expected (since we now know doc).
            # Use deterministic doc path insertion: quoted.
            for ni in sorted(unpaired_names):
                nline = lines[ni]
                m = NAME_RE.match(nline)
                if m:
                    rhs = quote_like(m.group("rhs"), exp_name)
                    prefix = m.group("prefix") or ""
                    lines[ni] = f"{prefix}SV_CONTRACT_NAME={rhs}"

                # Insert DOC below
                insert_at = ni + 1
                rhs_doc = quote_like('"X"', inferred_doc_rel)
                # mirror export-ness from NAME line if it had export
                export_prefix = ""
                if nline.lstrip().startswith("export "):
                    export_prefix = "export "
                lines.insert(insert_at, f"{export_prefix}SV_CONTRACT_DOC_PATH={rhs_doc}")
                changed = True

                per_doc.setdefault(inferred_doc_rel, set()).add(rel_script)
        else:
            # Ambiguous or absent: deterministic error listing script.
            offs = ", ".join(str(i + 1) for i in sorted(unpaired_names))
            if len(candidates) == 0:
                die(
                    f"{rel_script}: SV_CONTRACT_NAME present but no SV_CONTRACT_DOC_PATH, and script is not uniquely "
                    f"referenced by exactly one contract doc's Enforced By. Offending NAME line(s) (1-indexed): {offs}"
                )
            else:
                die(
                    f"{rel_script}: SV_CONTRACT_NAME present but no SV_CONTRACT_DOC_PATH, and script is referenced by "
                    f"multiple contract docs' Enforced By so inference is ambiguous. Candidates: {', '.join(stable_sorted(candidates))}. "
                    f"Offending NAME line(s) (1-indexed): {offs}"
                )

    new_txt = "\n".join(lines).rstrip("\n") + "\n"
    if changed:
        write_text_if_changed(script, new_txt)

    return changed, per_doc


def main() -> None:
    os.chdir(REPO_ROOT)

    # Phase A: Strong removal from non-enforcement scripts
    remove_markers_from_non_enforcement_scripts()

    # Phase B: Build doc index for inference (from current docs state)
    doc_enforced_by_index = build_existing_doc_enforced_by_index()

    # Phase C: Scan enforcement scripts and canonicalize markers; build reverse map doc -> enforcers
    doc_to_enforcers: Dict[str, Set[str]] = {}

    enforcement_scripts = sorted([p for p in SCRIPTS_DIR.glob("*.sh") if is_enforcement_script(p)])
    for script in enforcement_scripts:
        txt = read_text(script)
        lines = txt.split("\n")
        decls = find_decl_lines(lines)
        pairs, unpaired_names, unpaired_docs = pair_decls(decls, window=5)

        _changed, per_doc = rewrite_script_with_pairs(
            script=script,
            pairs=pairs,
            unpaired_names=unpaired_names,
            unpaired_docs=unpaired_docs,
            doc_enforced_by_index=doc_enforced_by_index,
        )
        for doc_rel, enfs in per_doc.items():
            doc_to_enforcers.setdefault(doc_rel, set()).update(enfs)

    # Phase D: Doc canonicalization
    docs = load_contract_docs()
    for doc in docs:
        doc_rel = script_rel(doc)

        # Reverse-scanned declarers from enforcement script markers.
        enforcers = set(doc_to_enforcers.get(doc_rel, set()))

        # If reverse-scan yields empty, fall back to existing valid enforcement bullets
        # (filtered to enforcement surfaces that exist). This preserves repo proof contracts.
        if not enforcers:
            existing = []
            md0 = read_text(doc)
            for b in parse_enforced_by_bullets(md0):
                if (b.startswith("scripts/gate_") or b.startswith("scripts/prove_")) and (REPO_ROOT / b).exists():
                    existing.append(b)
            enforcers.update(existing)

        # Validate and strip non-enforcement entries by construction; also require that referenced scripts exist.
        new_md = canonicalize_enforced_by(read_text(doc), stable_sorted(enforcers))
        write_text_if_changed(doc, new_md)

    note("OK: contract surface autosync v2 patcher complete.")


if __name__ == "__main__":
    main()
