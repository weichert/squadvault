from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent

# === Canonical targets (v1: hardcoded, fail-closed) ===
PROOF_REGISTRY = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")
CI_GUARDRAILS_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
CI_ENTRYPOINT = Path("scripts/prove_ci.sh")

# === Documentation maps to parse (v1: text only; deterministic) ===
DOC_MAPS_V1 = [
    Path("docs/canonical/Documentation_Map_and_Canonical_References.md"),
    Path("docs/80_indices/signal_scout/Documentation_Map_Tier2_Addition_v1.4.md"),
]
LEGACY_SIGNATURE_EXCEPTIONS_V1 = [
    'docs/80_indices/ops/Golden_Path_Pytest_Pinning_v1.0.md',
    'docs/80_indices/signal_scout/Documentation_Map_Tier2_Addition_v1.4.md',
    'docs/canon_pointers/How_to_Read_SquadVault_v1.0.md',
    'docs/canon_pointers/signal_taxonomy_v1.1.md',
]


# === New artifacts ===
NEW_PROOF_RUNNER = Path("scripts/prove_docs_integrity_v1.sh")
NEW_CHECKER = Path("scripts/check_docs_integrity_v1.py")
NEW_INVARIANT = Path("docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md")

PATCH_SUCCESS = "PATCH_APPLIED: docs integrity gate v1"
PATCH_NOOP = "NO-OP (v1): docs integrity gate already present and identical"


V1_CANON_ROOT_CANDIDATES = [
    "docs/canonical",
    "docs/30_contract_cards",
    "docs/40_specs",
    "docs/80_indices",
    "docs/canon_pointers",
]

CANON_HEADER = "[SV_CANONICAL_HEADER_V1]"


def die(msg: str) -> None:
    raise SystemExit(msg)


def read_text(p: Path) -> str:
    return (REPO_ROOT / p).read_text(encoding="utf-8")


def write_text(p: Path, s: str) -> None:
    out = REPO_ROOT / p
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s, encoding="utf-8", newline="\n")


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def ensure_exists(p: Path) -> None:
    if not (REPO_ROOT / p).exists():
        die(f"FAIL: required canonical file missing: {p}")


def canonical_roots_v1() -> List[str]:
    roots: List[str] = []
    for rel in V1_CANON_ROOT_CANDIDATES:
        if (REPO_ROOT / rel).exists():
            roots.append(rel)
    roots = sorted(roots)
    if not roots:
        die("FAIL: no canonical doc roots found from v1 candidate list; cannot proceed safely.")
    return roots


def insert_after_anchor_or_fail(text: str, anchor_re: str, insertion: str) -> Tuple[str, bool]:
    m = re.search(anchor_re, text, flags=re.MULTILINE)
    if not m:
        die(f"FAIL: insertion anchor not found: {anchor_re!r}")
    idx = m.end()
    prefix = "" if text[:idx].endswith("\n") else "\n"
    new_text = text[:idx] + prefix + insertion + text[idx:]
    return new_text, True


def ensure_contains_or_insert_once(text: str, needle: str, anchor_re: str, insertion: str) -> Tuple[str, bool]:
    if needle in text:
        return text, False
    return insert_after_anchor_or_fail(text, anchor_re, insertion)


def new_proof_runner_sh() -> str:
    return """\
#!/usr/bin/env bash
set -euo pipefail

# CWD-independent: resolve repo root relative to this script
here="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"

python_bin="${PYTHON:-python}"

echo "==> Docs integrity gate (v1)"
"$python_bin" "$repo_root/scripts/check_docs_integrity_v1.py"
echo "OK: docs integrity gate (v1) passed"
"""


def new_checker_py(roots: List[str]) -> str:
    roots_py = "[" + ", ".join(repr(r) for r in roots) + "]"
    doc_maps_py = "[" + ", ".join(repr(str(p)) for p in DOC_MAPS_V1) + "]"

    return f"""\
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parent.parent

# v1 LOCK: canonical roots allowlist (frozen at patch time)
CANONICAL_ROOTS_V1 = {roots_py}

# v1 LOCK: canonical header marker
CANON_HEADER = {CANON_HEADER!r}

# v1 LOCK: documentation maps (text only)
DOC_MAPS_V1 = {doc_maps_py}

VERSIONED_RE = re.compile(r"_v\\d+\\.\\d+", re.IGNORECASE)
MD_LINK_RE = re.compile(r"\\]\\(([^)]+)\\)")
PATH_TOKEN_RE = re.compile(r"(docs/[A-Za-z0-9_\\-./]+|scripts/[A-Za-z0-9_\\-./]+)")

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
        die(f"FAIL: canonical root missing: {{rel_root}}")
    files = [p for p in root.rglob("*") if p.is_file()]
    return sorted(files, key=lambda x: str(x))

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

def gate_canonical_signature_on_versioned(files: List[Path]) -> None:
    # v1 canonical signature rules must match existing repo reality.
    # Accept any of:
    # - [SV_CANONICAL_HEADER_V1] marker anywhere in first 40 lines
    # - "Status: CANONICAL" anywhere in first 60 lines
    # - H1 line containing "(vX.Y)" in first 20 lines
    H1_VER_RE = re.compile(r"^#\\s+.*\\(v\\d+\\.\\d+\\)", re.IGNORECASE)
    STATUS_CANON_RE = re.compile(r"^Status:\\s*CANONICAL\\b", re.IGNORECASE)

    def signature_present(p: Path) -> bool:
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return False

        head_40 = "\\n".join(lines[:40])
        if "[SV_CANONICAL_HEADER_V1]" in head_40:
            return True

        for ln in lines[:60]:
            if STATUS_CANON_RE.search(ln):
                return True

        for ln in lines[:20]:
            if H1_VER_RE.search(ln):
                return True

        return False

    missing: List[str] = []
    for p in files:
        if not is_versioned_text_doc(p):
            continue
        LEGACY_SIGNATURE_EXCEPTIONS_V1 = set([
            'docs/80_indices/ops/Golden_Path_Pytest_Pinning_v1.0.md',
            'docs/80_indices/signal_scout/Documentation_Map_Tier2_Addition_v1.4.md',
            'docs/canon_pointers/How_to_Read_SquadVault_v1.0.md',
            'docs/canon_pointers/signal_taxonomy_v1.1.md',
        ])

        rp = rel(p)
        if rp in LEGACY_SIGNATURE_EXCEPTIONS_V1:
            continue
        if not signature_present(p):
            missing.append(rel(p))
    if missing:
        die(
            "FAIL: versioned canonical artifacts missing canonical signature.\\n"
            "Accepted signatures (v1):\\n"
            "  - [SV_CANONICAL_HEADER_V1] within first 40 lines\\n"
            "  - 'Status: CANONICAL' within first 60 lines\\n"
            "  - H1 containing '(vX.Y)' within first 20 lines\\n\\n"
            "Missing:\\n" + "\\n".join(sorted(missing))
        )

def gate_duplicate_basenames(files: List[Path]) -> None:
    seen: Dict[str, str] = {{}}
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
            dups.append(f"{{base}}:\\n  - {{seen[base]}}\\n  - {{r}}")
        else:
            seen[base] = r
    if dups:
        die("FAIL: duplicate canonical basenames detected (case-sensitive):\\n" + "\\n\\n".join(sorted(dups)))

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
        die("FAIL: documentation map references missing paths:\\n" + "\\n".join(missing))

def gate_ci_index_coverage(ci_index: Path) -> None:
    txt = ci_index.read_text(encoding="utf-8", errors="replace")
    # Minimal + explicit: index must reference invariant and the new runner name
    inv = "docs/80_indices/ops/Docs_Integrity_Gate_Invariant_v1.0.md"
    inv_rel = "./Docs_Integrity_Gate_Invariant_v1.0.md"
    runner = "scripts/prove_docs_integrity_v1.sh"
    missing: List[str] = []
    if (inv not in txt) and (inv_rel not in txt):
        missing.append(f"missing ref/link to invariant doc: {{inv}} (or {{inv_rel}})")
    if runner not in txt:
        missing.append(f"missing ref/link to proof runner: {{runner}}")
    if missing:
        die("FAIL: CI guardrails index coverage gate failed:\\n- " + "\\n- ".join(missing))

def main() -> None:
    # Validate doc maps exist (fail-closed)
    doc_maps: List[Path] = []
    for s in DOC_MAPS_V1:
        p = REPO_ROOT / s
        if not p.exists():
            die(f"FAIL: required documentation map missing (v1): {{s}}")
        doc_maps.append(p)

    canon_files: List[Path] = []
    for rel_root in CANONICAL_ROOTS_V1:
        canon_files.extend(sorted_files_under(rel_root))

    gate_canonical_signature_on_versioned(canon_files)
    gate_duplicate_basenames(canon_files)

    refs = extract_doc_map_refs(doc_maps)
    gate_doc_map_refs_exist(refs)

    ci_index = REPO_ROOT / "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
    if not ci_index.exists():
        die("FAIL: CI guardrails index missing: docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")
    gate_ci_index_coverage(ci_index)

if __name__ == "__main__":
    main()
"""


def new_invariant_doc_md(roots: List[str]) -> str:
    roots_block = "\n".join(f"- `{r}/...`" for r in roots)
    return f"""\
{CANON_HEADER}
Contract Name: Docs Integrity Gate Invariant
Version: v1.0
Status: CANONICAL — FROZEN

Defers To:
  - SquadVault — Canonical Operating Constitution (Tier 0)
  - SquadVault — Ops Shim & CWD Independence Contract (Ops)
  - SquadVault Development Playbook (MVP)

Default: Any behavior not explicitly permitted by this invariant is forbidden.

—

# SquadVault — Docs Integrity Gate Invariant (v1.0)

## Objective

Enforce **structural documentation governance invariants** for canonical SquadVault documentation.

This gate is **fail-closed** and **deterministic**.

## What This Gate Checks (Structural Only)

1) **Canonical header presence (structural)**
- For versioned canonical artifact-like filenames (containing `_vX.Y`) under canonical roots, require the canonical header marker:
  - `{CANON_HEADER}`

2) **Duplicate canonical artifact basenames**
- If two canonical-looking artifacts in canonical roots share the same basename (case-sensitive), fail.

3) **Documentation map pointer resolution**
- Parse **text documentation maps only** (v1 allowlist) and extract repo-local `docs/...` and `scripts/...` references.
- Any referenced path must exist.

4) **Index coverage (minimal)**
- Ensure the CI guardrails index references:
  - this invariant doc, and
  - the docs integrity proof runner.

## Out of Scope (Explicit)

- Semantic interpretation or contradiction detection
- Doc refactors or folder reorganizations
- Auto-fixing or rewriting docs
- New product features or runtime behavior changes
- Any weakening of CI enforcement or bypassing proof registry

## Legacy Signature Exceptions (v1)

The following versioned canonical files predate the signature convention. They are allowlisted in v1 to avoid a format-only migration:

- `docs/80_indices/ops/Golden_Path_Pytest_Pinning_v1.0.md`
- `docs/80_indices/signal_scout/Documentation_Map_Tier2_Addition_v1.4.md`
- `docs/canon_pointers/How_to_Read_SquadVault_v1.0.md`
- `docs/canon_pointers/signal_taxonomy_v1.1.md`

Any new versioned canonical doc MUST include an accepted canonical signature. Expanding this exception list requires v2.

## Canonical Roots Allowlist (v1 Locked)

This gate scans only these canonical roots (v1):

{roots_block}

Expanding this list requires a v2 patch (explicit version bump).

## Determinism + Fail-Closed

- Sorted traversal everywhere
- Stable parsing heuristics
- No network access
- Fail closed on ambiguity or missing canonical targets

## Remediation

If the gate fails:
- Add `{CANON_HEADER}` to missing versioned canonical artifacts.
- Rename/remove duplicates so basenames are unique across canonical roots.
- Fix documentation map references to point to existing repo-local paths.
- Ensure the CI guardrails index references this invariant and the proof runner.

## Canonical References

- CI Guardrails Index: `docs/80_indices/ops/CI_Guardrails_Index_v1.0.md`
- CI Proof Surface Registry: `docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md`
- Docs Integrity Proof Runner: `scripts/prove_docs_integrity_v1.sh`
"""


def main() -> None:
    # Fail-closed canonical file existence
    ensure_exists(PROOF_REGISTRY)
    ensure_exists(CI_GUARDRAILS_INDEX)
    ensure_exists(CI_ENTRYPOINT)
    for p in DOC_MAPS_V1:
        ensure_exists(p)

    roots = canonical_roots_v1()

    want_runner = new_proof_runner_sh()
    want_checker = new_checker_py(roots)
    want_invariant = new_invariant_doc_md(roots)

    # Read current canonical files
    pr = read_text(PROOF_REGISTRY)
    ci = read_text(CI_GUARDRAILS_INDEX)
    prove_ci = read_text(CI_ENTRYPOINT)

    # --- Patch 1: add runner to proof surface registry under exact header ---
    pr_anchor = r"(?m)^##\s+Proof Runners\s+\(invoked by scripts/prove_ci\.sh\)\s*$"
    pr_line = "- scripts/prove_docs_integrity_v1.sh — Proves canonical docs structural governance invariants (fail-closed).\n"
    pr2, pr_changed = ensure_contains_or_insert_once(pr, "scripts/prove_docs_integrity_v1.sh", pr_anchor, pr_line)

    # --- Patch 2: add guardrail section to CI guardrails index under Active Guardrails ---
    ci_anchor = r"(?m)^##\s+Active Guardrails\s*$"
    ci_block = """\
### Docs Integrity Guardrail
- **Status:** ACTIVE (enforced)
- **Entrypoint:** `scripts/prove_ci.sh`
- **Enforcement:** `scripts/prove_docs_integrity_v1.sh`
- **Invariant:** Enforces structural governance invariants for canonical docs; fail-closed.
- **Details:**  
  → [Docs_Integrity_Gate_Invariant_v1.0.md](./Docs_Integrity_Gate_Invariant_v1.0.md)

"""
    ci2, ci_changed = ensure_contains_or_insert_once(ci, "Docs Integrity Guardrail", ci_anchor, ci_block)

    # Also ensure the Proof Surface section references remain (already present), but require runner mention too.
    # We'll insert the runner path near Proof Surface header if not present.
    ps_anchor = r"(?m)^##\s+Proof Surface\s*$"
    ci2, ci_changed2 = ensure_contains_or_insert_once(
        ci2,
        "scripts/prove_docs_integrity_v1.sh",
        ps_anchor,
        "- scripts/prove_docs_integrity_v1.sh — Docs integrity proof runner (v1).\n\n",
    )
    ci_changed = ci_changed or ci_changed2

    # --- Patch 3: add invocation to scripts/prove_ci.sh in the proof suite (registry mechanism enforced elsewhere) ---
    # Insert immediately after check_no_pytest_directory_invocation, before proof runners begin.
    prove_anchor = r"(?m)^bash scripts/check_no_pytest_directory_invocation\.sh\s*$"
    prove_insert = "bash scripts/prove_docs_integrity_v1.sh\n"
    prove_ci2, prove_changed = ensure_contains_or_insert_once(
        prove_ci,
        "bash scripts/prove_docs_integrity_v1.sh",
        prove_anchor,
        prove_insert,
    )

    # --- Write new files (or validate identical) ---
    existing_ok = True
    if (REPO_ROOT / NEW_PROOF_RUNNER).exists():
        existing_ok &= (read_text(NEW_PROOF_RUNNER) == want_runner)
    if (REPO_ROOT / NEW_CHECKER).exists():
        existing_ok &= (read_text(NEW_CHECKER) == want_checker)
    if (REPO_ROOT / NEW_INVARIANT).exists():
        existing_ok &= (read_text(NEW_INVARIANT) == want_invariant)

    # If everything already matches exactly, NO-OP
    if existing_ok and (not pr_changed) and (not ci_changed) and (not prove_changed):
        print(PATCH_NOOP)
        return

    # Apply writes
    write_text(NEW_PROOF_RUNNER, want_runner)
    write_text(NEW_CHECKER, want_checker)
    write_text(NEW_INVARIANT, want_invariant)

    if pr2 != pr:
        write_text(PROOF_REGISTRY, pr2)
    if ci2 != ci:
        write_text(CI_GUARDRAILS_INDEX, ci2)
    if prove_ci2 != prove_ci:
        write_text(CI_ENTRYPOINT, prove_ci2)

    print(PATCH_SUCCESS)


if __name__ == "__main__":
    main()
