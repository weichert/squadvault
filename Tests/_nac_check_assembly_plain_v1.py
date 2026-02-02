#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_MARKERS = [
    r"^NON-CANONICAL — Narrative Assembly Export$",
    r"^## Provenance$",
    r"^## Writing Room \(SelectionSetV1\)$",
    r"^<!-- BEGIN_WRITING_ROOM_SELECTION_SET_V1 -->$",
    r"^<!-- END_WRITING_ROOM_SELECTION_SET_V1 -->$",
    r"^## Window — canonical$",
    r"^<!-- BEGIN_CANONICAL_WINDOW -->$",
    r"^<!-- END_CANONICAL_WINDOW -->$",
    r"^<!-- BEGIN_CANONICAL_FINGERPRINT -->$",
    r"^<!-- END_CANONICAL_FINGERPRINT -->$",
    r"^## What happened \(facts\) — canonical$",
    r"^<!-- BEGIN_CANONICAL_FACTS -->$",
    r"^<!-- END_CANONICAL_FACTS -->$",
    r"^## Counts — canonical$",
    r"^<!-- BEGIN_CANONICAL_COUNTS -->$",
    r"^<!-- END_CANONICAL_COUNTS -->$",
    r"^## Traceability — canonical$",
    r"^<!-- BEGIN_CANONICAL_TRACE -->$",
    r"^<!-- END_CANONICAL_TRACE -->$",
]

def die(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(2)

def main() -> int:
    if len(sys.argv) != 2:
        die("usage: _nac_check_assembly_plain_v1.py <path-to-assembly_plain_v1.md>")

    p = Path(sys.argv[1])
    if not p.exists():
        die(f"file not found: {p}")

    text = p.read_text(encoding="utf-8")

    # 1) Required markers
    for pat in REQUIRED_MARKERS:
        if not re.search(pat, text, flags=re.MULTILINE):
            die(f"missing required marker: {pat}")

    # 2) Fingerprint consistency
    m_block = re.search(
        r"<!-- BEGIN_CANONICAL_FINGERPRINT -->\s*Selection fingerprint:\s*([0-9a-f]{64})\s*<!-- END_CANONICAL_FINGERPRINT -->",
        text,
        flags=re.MULTILINE,
    )
    if not m_block:
        die("could not parse fingerprint from BEGIN_CANONICAL_FINGERPRINT block")
    fp_block = m_block.group(1)

    m_any = re.search(r"^Selection fingerprint:\s*([0-9a-f]{64})$", text, flags=re.MULTILINE)
    if not m_any:
        die("could not find any 'Selection fingerprint:' line")
    fp_any = m_any.group(1)

    if fp_block != fp_any:
        die(f"fingerprint mismatch: block={fp_block} vs line={fp_any}")

    # 3) Facts bullets present
    m_facts = re.search(
        r"<!-- BEGIN_CANONICAL_FACTS -->\s*(.*?)\s*<!-- END_CANONICAL_FACTS -->",
        text,
        flags=re.DOTALL,
    )
    if not m_facts:
        die("could not extract canonical facts block")

    facts = m_facts.group(1)
    if "What happened (facts)" not in facts:
        die("canonical facts block missing 'What happened (facts)' header")
    if not re.search(r"^\- ", facts, flags=re.MULTILINE):
        die("canonical facts block has no bullets")

    # 4) Trace block label correctness
    m_trace = re.search(
        r"<!-- BEGIN_CANONICAL_TRACE -->\s*(.*?)\s*<!-- END_CANONICAL_TRACE -->",
        text,
        flags=re.DOTALL,
    )
    if not m_trace:
        die("could not extract canonical trace block")

    trace_block = m_trace.group(1)
    if "Trace (canonical_event ids):" not in trace_block:
        die("canonical trace block must label ids as canonical_event ids")

    print("OK: NAC assembly_plain_v1 structure looks stable.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
