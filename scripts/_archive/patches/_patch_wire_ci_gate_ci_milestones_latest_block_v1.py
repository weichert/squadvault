from __future__ import annotations

from pathlib import Path
import re
import sys

PROVE = Path("scripts/prove_ci.sh")
OPS_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

GATE_LINE = 'bash "$REPO_ROOT/scripts/gate_ci_milestones_latest_block_v1.sh"'
GATE_HEADER = "=== Gate: CI Milestones Latest bounded block (v1) ==="

def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"ERR: missing file: {p}")

def _write_if_changed(p: Path, new: str, old: str, label: str) -> None:
    if new == old:
        print(f"OK: {label} already canonical (noop)")
        return
    p.write_text(new, encoding="utf-8")
    print(f"OK: {label} patched")

def patch_prove_ci() -> None:
    text = _read(PROVE)

    if "gate_ci_milestones_latest_block_v1.sh" in text:
        _write_if_changed(PROVE, text, text, "prove_ci wiring")
        return

    # Prefer inserting right after docs integrity gate if present
    anchors = [
        "gate_docs_integrity",
        "Docs integrity",
        "docs integrity",
    ]

    insert_pos = None
    for a in anchors:
        idx = text.find(a)
        if idx != -1:
            # insert after the line containing the anchor
            line_end = text.find("\n", idx)
            insert_pos = line_end + 1 if line_end != -1 else len(text)
            break

    if insert_pos is None:
        # fallback: before final OK line if present, else append
        m_ok = re.search(r"^OK:.*$", text, flags=re.M)
        insert_pos = m_ok.start() if m_ok else len(text)

    block = (
        f'\necho "{GATE_HEADER}"\n'
        f"{GATE_LINE}\n"
    )

    new = text[:insert_pos] + block + text[insert_pos:]
    _write_if_changed(PROVE, new, text, "prove_ci wiring")

def patch_ops_index() -> None:
    text = _read(OPS_INDEX)

    bullet = "- CI Milestones Latest bounded block gate (v1) — scripts/gate_ci_milestones_latest_block_v1.sh"
    if bullet in text:
        _write_if_changed(OPS_INDEX, text, text, "Ops index")
        return

    # Try to add under a plausible CI gates section header
    headers = [
        "## CI Gates",
        "## Gates",
        "## CI Guardrails",
    ]

    for h in headers:
        m = re.search(rf"^{re.escape(h)}\s*$", text, flags=re.M)
        if m:
            # insert after header line
            line_end = text.find("\n", m.end())
            ins = line_end + 1 if line_end != -1 else len(text)
            new = text[:ins] + f"{bullet}\n" + text[ins:]
            _write_if_changed(OPS_INDEX, new, text, "Ops index")
            return

    # Fallback: append a minimal section at end
    new = text.rstrip() + "\n\n## CI Gates\n" + f"{bullet}\n"
    _write_if_changed(OPS_INDEX, new, text, "Ops index")

def main() -> None:
    patch_prove_ci()
    patch_ops_index()

if __name__ == "__main__":
    main()
