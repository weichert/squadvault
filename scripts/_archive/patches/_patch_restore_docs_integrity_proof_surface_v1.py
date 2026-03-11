from __future__ import annotations

from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")
GATE = Path("scripts/gate_docs_integrity_v2.sh")

NEEDLE_PROOF = "bash scripts/prove_docs_integrity_v1.sh\n"

# Insert the proof call immediately after the docs_integrity (v2) gate block end marker.
AFTER_LINE = "# SV_GATE: docs_integrity (v2) end\n"

def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def _rewrite_gate_v2(text: str) -> str:
    # Remove the baseline docs integrity proof call from the gate.
    # We specifically remove the "Baseline docs integrity proof" section to avoid double-running.
    lines = text.splitlines(True)
    out: list[str] = []

    skipping = False
    removed = False

    for ln in lines:
        if (not skipping) and ("Baseline docs integrity proof" in ln or "Baseline docs integrity" in ln):
            skipping = True
            removed = True
            continue

        if skipping:
            # stop skipping once we hit the marker-enforcement section header
            if "Marker exact-once enforcement" in ln or "Marker exact-once" in ln:
                skipping = False
                out.append(ln)
            # else keep skipping
            continue

        # Also defensively drop a direct bash call to prove_docs_integrity_v1 if present
        if 'bash "scripts/prove_docs_integrity_v1.sh"' in ln or "bash scripts/prove_docs_integrity_v1.sh" in ln:
            removed = True
            continue

        out.append(ln)

    new_text = "".join(out)
    # If we didn't find the section header pattern, we still might have removed direct bash line above.
    # If nothing changed, return original.
    return new_text if new_text != text else text

def _insert_proof_call_into_prove_ci(text: str) -> str:
    # Idempotent: if already present, no-op.
    if NEEDLE_PROOF in text:
        return text

    if AFTER_LINE not in text:
        raise SystemExit(f"expected marker not found in {PROVE}: {AFTER_LINE.strip()}")

    parts = text.split(AFTER_LINE)
    if len(parts) != 2:
        raise SystemExit("expected docs_integrity (v2) end marker to appear exactly once")

    head, tail = parts
    # ensure exactly one newline separation
    insertion = AFTER_LINE + "\n" + NEEDLE_PROOF + "\n"
    return head + insertion + tail.lstrip("\n")

def main() -> None:
    if not PROVE.exists():
        raise SystemExit(f"missing canonical file: {PROVE}")
    if not GATE.exists():
        raise SystemExit(f"missing canonical file: {GATE}")

    # 1) Update gate_docs_integrity_v2.sh to NOT run the proof (gate-only)
    gate_text = _read(GATE)
    gate_new = _rewrite_gate_v2(gate_text)
    if gate_new != gate_text:
        _write(GATE, gate_new)

    # 2) Re-add direct proof invocation to prove_ci.sh so registry gate is satisfied
    prove_text = _read(PROVE)
    prove_new = _insert_proof_call_into_prove_ci(prove_text)
    if prove_new != prove_text:
        _write(PROVE, prove_new)

if __name__ == "__main__":
    main()
