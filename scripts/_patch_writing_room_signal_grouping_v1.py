from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "selection_set_schema_v1.py"
INTAKE = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "intake_v1.py"

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def must_exist(p: Path) -> None:
    if not p.exists():
        die(f"Missing file: {p}")

def must_contain(p: Path, needle: str) -> None:
    s = p.read_text(encoding="utf-8")
    if needle not in s:
        die(f"{p} missing required needle: {needle!r}")

def write_if_changed(p: Path, new: str) -> None:
    old = p.read_text(encoding="utf-8")
    if old == new:
        print(f"OK: {p.relative_to(ROOT)} unchanged")
        return
    p.write_text(new, encoding="utf-8")
    print(f"OK: updated {p.relative_to(ROOT)} ({len(old)} -> {len(new)} bytes)")

def patch_selection_set_schema() -> None:
    must_exist(SEL)
    s = SEL.read_text(encoding="utf-8")

    # Fail fast anchors
    must_contain(SEL, "class GroupBasisCode")
    must_contain(SEL, "class SignalGrouping")
    must_contain(SEL, "sha256")  # your module likely already has a sha helper or uses hashlib

    if "def build_signal_groupings_v1(" in s:
        die("selection_set_schema_v1.py already contains build_signal_groupings_v1; refusing to patch twice.")

    helper_block = r'''

# -----------------------------
# SignalGrouping generation (v1)
# -----------------------------

from dataclasses import dataclass
from typing import Callable, Iterable

@dataclass(frozen=True)
class SignalGroupingExtractorV1:
    """
    Adapter contract: signals are opaque objects.
    No new Signal schema is introduced here.
    """
    get_signal_id: Callable[[object], str]
    get_scope_key: Callable[[object], str]
    get_subject_key: Callable[[object], str]
    get_fact_basis_keys: Callable[[object], Iterable[str]]

def _norm_keys(xs: Iterable[str] | str | None) -> list[str]:
    if xs is None:
        return []
    if isinstance(xs, (list, tuple)):
        return [str(x) for x in xs]
    return [str(xs)]

def _sha256_hex(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _group_id_v1(group_basis: str, scope_key: str, subject_key: str, fact_basis_key: str) -> str:
    canonical = f"SignalGrouping|v1.0|{group_basis}|scope={scope_key}|subject={subject_key}|fact={fact_basis_key}"
    return _sha256_hex(canonical)

def build_signal_groupings_v1(
    included_signals: list[object],
    extractor: SignalGroupingExtractorV1,
) -> list["SignalGrouping"]:
    """
    Deterministic grouping v1:
      - eligibility: SAME_SCOPE + SAME_SUBJECT + SHARED_FACT_BASIS
      - emitted basis: SHARED_FACT_BASIS
      - ordering: groupings sorted by group_id; signal_ids lexicographically sorted
    """
    # Buckets keyed by (scope, subject, fact_basis_key)
    buckets: dict[tuple[str, str, str], list[str]] = {}

    for sig in included_signals:
        sid = str(extractor.get_signal_id(sig))
        scope_key = str(extractor.get_scope_key(sig))
        subject_key = str(extractor.get_subject_key(sig))
        fact_keys = sorted(_norm_keys(extractor.get_fact_basis_keys(sig)))

        # No inference: missing keys => not eligible for grouping
        if not scope_key or not subject_key or not fact_keys:
            continue

        for fk in fact_keys:
            buckets.setdefault((scope_key, subject_key, fk), []).append(sid)

    groupings: list[SignalGrouping] = []
    for (scope_key, subject_key, fk), sids in buckets.items():
        uniq = sorted(set(sids))
        if len(uniq) < 2:
            continue

        gid = _group_id_v1("SHARED_FACT_BASIS", scope_key, subject_key, fk)
        groupings.append(
            SignalGrouping(
                group_id=gid,
                group_basis=GroupBasisCode.SHARED_FACT_BASIS,
                signal_ids=uniq,
                group_label=None,
            )
        )

    groupings.sort(key=lambda g: g.group_id)
    return groupings
'''

    # Append at end (low-risk, no fragile AST rewrites)
    write_if_changed(SEL, s + helper_block)

def patch_intake() -> None:
    must_exist(INTAKE)
    s = INTAKE.read_text(encoding="utf-8")

    # Fail fast anchors
    must_contain(INTAKE, "SelectionSet")
    must_contain(INTAKE, "included_signal_ids")

    if "build_signal_groupings_v1" in s:
        die("intake_v1.py already references build_signal_groupings_v1; refusing to patch twice.")

    # Ensure import exists (add next to other schema imports)
    if "SignalGroupingExtractorV1" not in s:
        # Try to extend an existing import-from selection_set_schema_v1 line.
        m = re.search(r"^from \.selection_set_schema_v1 import (.+)$", s, flags=re.M)
        if not m:
            die("Could not find import line: from .selection_set_schema_v1 import ... (add one, then rerun)")
        line = m.group(0)
        imports = m.group(1)
        # Add needed names if not already there
        needed = ["build_signal_groupings_v1", "SignalGroupingExtractorV1"]
        for name in needed:
            if name not in imports:
                imports = imports.rstrip() + f", {name}"
        s = s.replace(line, f"from .selection_set_schema_v1 import {imports}")

    # Add grouping_extractor param to build_selection_set_v1
    fn = re.search(r"def build_selection_set_v1\(([\s\S]*?)\)\s*->", s)
    if not fn:
        die("Could not locate def build_selection_set_v1(...)-> ... in intake_v1.py")
    sig_block = fn.group(0)
    if "grouping_extractor" not in sig_block:
        # Insert before closing paren of signature.
        s = s.replace(
            sig_block,
            sig_block.replace(")\s*->", ",\n    grouping_extractor: SignalGroupingExtractorV1 | None = None,\n) ->")
        )

    # Compute groupings right before SelectionSet(...) construction.
    idx = s.rfind("SelectionSet(")
    if idx == -1:
        die("Could not find SelectionSet( construction in intake_v1.py")

    if "groupings =" not in s[:idx]:
        inject = "\n    groupings = None\n    if grouping_extractor is not None:\n        groupings = build_signal_groupings_v1(included_signals, grouping_extractor)\n\n"
        s = s[:idx] + inject + s[idx:]

    # Add groupings= to SelectionSet(...) if not present
    if "groupings=" in s[idx: idx + 400]:
        die("SelectionSet(...) already has groupings=; refusing to patch.")
    s = s[:idx] + s[idx:].replace("SelectionSet(\n", "SelectionSet(\n        groupings=groupings,\n", 1)

    write_if_changed(INTAKE, s)

def main() -> int:
    print("=== Patch: Writing Room SignalGrouping v1 (deterministic) ===")
    print(f"repo_root: {ROOT}")
    print(f"target:    {SEL.relative_to(ROOT)}")
    print(f"target:    {INTAKE.relative_to(ROOT)}\n")

    patch_selection_set_schema()
    patch_intake()

    print("\nNext:")
    print("  ./scripts/py -c \"from squadvault.recaps.writing_room.selection_set_schema_v1 import build_signal_groupings_v1; print('import ok')\"")
    print("  pytest")
    print("  ./scripts/test.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
