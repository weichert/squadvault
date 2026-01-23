from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "src" / "squadvault" / "recaps" / "writing_room" / "intake_v1.py"

NEEDED_IMPORT = "build_signal_groupings_v1"
NEEDED_IMPORT2 = "SignalGroupingExtractorV1"  # optional, for type clarity if you want it imported

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def must_exist(p: Path) -> None:
    if not p.exists():
        die(f"Missing file: {p}")

def write_if_changed(p: Path, new: str) -> None:
    old = p.read_text(encoding="utf-8")
    if old == new:
        print(f"OK: {p.relative_to(ROOT)} unchanged")
        return
    p.write_text(new, encoding="utf-8")
    print(f"OK: updated {p.relative_to(ROOT)} ({len(old)} -> {len(new)} bytes)")

def patch_imports(s: str) -> str:
    # If already present, noop
    if "build_signal_groupings_v1" in s:
        return s

    # Preferred: extend existing canonical import block from selection_set_schema_v1
    m = re.search(r"^from \.selection_set_schema_v1 import \(\n([\s\S]*?)\n\)\n", s, flags=re.M)
    if m:
        block = m.group(0)
        inner = m.group(1)

        # Fail-fast: ensure we don't double-insert
        if NEEDED_IMPORT in inner:
            return s

        # Insert near end, before closing paren.
        # Keep deterministic formatting: add one line with 4 spaces indent like others.
        inner2 = inner.rstrip() + f"\n    {NEEDED_IMPORT},\n"
        block2 = block.replace(inner, inner2, 1)
        return s.replace(block, block2, 1)

    # Fallback: insert a standalone import in the top import block
    lines = s.splitlines(True)
    last_import_idx = None
    for i, line in enumerate(lines):
        t = line.strip()
        if t == "" or t.startswith("#"):
            last_import_idx = i
            continue
        if t.startswith("from __future__ import "):
            last_import_idx = i
            continue
        if t.startswith("import ") or t.startswith("from "):
            last_import_idx = i
            continue
        break
    if last_import_idx is None:
        die("Could not locate safe import block to insert build_signal_groupings_v1 import.")

    insert_at = last_import_idx + 1
    ins = []
    if insert_at > 0 and lines[insert_at - 1].strip() != "":
        ins.append("\n")
    ins.append("from .selection_set_schema_v1 import build_signal_groupings_v1\n")
    if insert_at < len(lines) and lines[insert_at].strip() != "":
        ins.append("\n")
    return "".join(lines[:insert_at] + ins + lines[insert_at:])

def patch_included_signals_accumulator(s: str) -> str:
    # Add included_signals list right after included_ids initialization.
    if "included_signals:" in s:
        return s

    needle = "included_ids: list[str] = []"
    idx = s.find(needle)
    if idx == -1:
        die("Could not find 'included_ids: list[str] = []' anchor in intake_v1.py")

    insert = (
        "included_ids: list[str] = []\n"
        "    included_signals: list[Any] = []\n"
    )
    return s.replace(needle, insert, 1)

def patch_append_included_signals(s: str) -> str:
    # When included_ids.append(sid) happens, also append raw sig to included_signals.
    # Fail-fast if structure differs.
    if "included_signals.append(sig)" in s:
        return s

    needle = "included_ids.append(sid)"
    idx = s.find(needle)
    if idx == -1:
        die("Could not find 'included_ids.append(sid)' anchor in intake_v1.py")

    # Insert immediately after, with matching indent (8 spaces in your snippet).
    repl = "included_ids.append(sid)\n\n        included_signals.append(sig)"
    return s.replace(needle, repl, 1)

def patch_groupings_before_return(s: str) -> str:
    anchor = "return SelectionSetV1("
    idx = s.rfind(anchor)
    if idx == -1:
        die("Could not find 'return SelectionSetV1(' anchor in intake_v1.py")

    pre = s[:idx]
    post = s[idx:]

    if "included_signals" not in pre:
        die("included_signals not found before return; accumulator patch did not apply as expected.")

    if "groupings =" not in pre:
        inject = (
            "\n    groupings = None\n"
            "    grouping_extractor = kwargs.get('grouping_extractor')\n"
            "    if grouping_extractor is not None:\n"
            "        groupings = build_signal_groupings_v1(included_signals, grouping_extractor)\n\n"
        )
        pre = pre + inject

    # Inject groupings= into SelectionSetV1(...) args if not already present
    if "groupings=" in post[:600]:
        return pre + post

    post2 = post.replace(
        "return SelectionSetV1(\n",
        "return SelectionSetV1(\n        groupings=groupings,\n",
        1,
    )
    return pre + post2

def main() -> int:
    print("=== Patch: WR intake_v1 wire-up SignalGrouping v1 (v3) ===")
    print(f"repo_root: {ROOT}")
    print(f"target:    {INTAKE.relative_to(ROOT)}\n")

    must_exist(INTAKE)
    s = INTAKE.read_text(encoding="utf-8")

    # Fail-fast: ensure we are patching the right file type
    if "def build_selection_set_v1" not in s:
        die("intake_v1.py missing build_selection_set_v1; refusing to patch wrong file.")
    if "return SelectionSetV1(" not in s:
        die("intake_v1.py missing return SelectionSetV1( anchor; refusing to patch.")

    s2 = s
    s2 = patch_imports(s2)
    s2 = patch_included_signals_accumulator(s2)
    s2 = patch_append_included_signals(s2)
    s2 = patch_groupings_before_return(s2)

    write_if_changed(INTAKE, s2)

    print("\nNext:")
    print("  pytest")
    print("  ./scripts/test.sh")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
