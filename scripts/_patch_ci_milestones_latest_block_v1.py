from __future__ import annotations

from pathlib import Path
import re
import sys

DOC = Path("docs/logs/CI_MILESTONES.md")

BEGIN = "<!-- SV_CI_MILESTONES_LATEST_v1_BEGIN -->"
END   = "<!-- SV_CI_MILESTONES_LATEST_v1_END -->"

H2_LATEST_RE = re.compile(r"^##\s+Latest\s*$", re.M)
H2_ANY_RE = re.compile(r"^##\s+\S.*$", re.M)

def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"ERR: missing file: {p}")

def _write_if_changed(p: Path, new: str, old: str) -> None:
    if new == old:
        print("OK: CI_MILESTONES Latest block already canonical (noop)")
        return
    p.write_text(new, encoding="utf-8")
    print("OK: CI_MILESTONES Latest block patched")

def main() -> None:
    text = _read_text(DOC)

    b_ct = text.count(BEGIN)
    e_ct = text.count(END)
    if b_ct != e_ct:
        raise SystemExit(f"ERR: marker count mismatch: BEGIN={b_ct} END={e_ct}")

    if b_ct > 1:
        raise SystemExit("ERR: duplicated Latest block markers (refusing to guess)")

    if b_ct == 1:
        # Ensure ordering is sane
        b_idx = text.find(BEGIN)
        e_idx = text.find(END)
        if not (0 <= b_idx < e_idx):
            raise SystemExit("ERR: Latest markers out of order")
        _write_if_changed(DOC, text, text)
        return

    # No markers: attempt to wrap existing "## Latest" section if present.
    m = H2_LATEST_RE.search(text)
    if m:
        latest_start = m.start()
        # Find next H2 header after Latest (or EOF)
        m2 = H2_ANY_RE.search(text, pos=m.end())
        latest_end = m2.start() if m2 else len(text)

        before = text[:latest_start].rstrip("\n")
        latest_block = text[latest_start:latest_end].strip("\n")
        after = text[latest_end:].lstrip("\n")

        new = (
            f"{before}\n\n"
            f"{BEGIN}\n"
            f"{latest_block}\n"
            f"{END}\n\n"
            f"{after}"
        ).rstrip() + "\n"
        _write_if_changed(DOC, new, text)
        return

    # No "## Latest" section: insert a minimal bounded section near top (no placeholders).
    lines = text.splitlines(True)
    insert_at = 0

    # Prefer: after first H1 line and its immediate following blank line(s)
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            insert_at = j
            break

    latest_min_block = f"{BEGIN}\n## Latest\n\n{END}\n\n"

    new_lines = lines[:insert_at] + [latest_min_block] + lines[insert_at:]
    new = "".join(new_lines)
    _write_if_changed(DOC, new, text)

if __name__ == "__main__":
    main()
