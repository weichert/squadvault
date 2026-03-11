from __future__ import annotations

from pathlib import Path

PROVE_CI = Path("scripts/prove_ci.sh")
OPS_INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

INSERT_AFTER_LINE = "./scripts/check_time_timestamp_determinism.sh"
NEW_LINE = "bash scripts/gate_no_network_in_ci_proofs_v1.sh"

BEGIN_INDEX = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END_INDEX = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

BULLET = "- scripts/gate_no_network_in_ci_proofs_v1.sh — Forbid network/package-manager actions in CI proof surfaces (v1)"

def _read(p: Path) -> str:
    if not p.exists():
        raise SystemExit(f"missing file: {p}")
    return p.read_text(encoding="utf-8")

def _write_if_changed(p: Path, new: str) -> bool:
    old = _read(p)
    if old == new:
        return False
    p.write_text(new, encoding="utf-8")
    return True

def _insert_after_exact_line(text: str, after_line: str, new_line: str) -> str:
    lines = text.splitlines()

    # NOOP if already present
    if any(l.strip() == new_line.strip() for l in lines):
        return text

    out: list[str] = []
    inserted = False
    for ln in lines:
        out.append(ln)
        if (not inserted) and (ln.strip() == after_line.strip()):
            out.append(new_line)
            inserted = True

    if not inserted:
        raise SystemExit(f"anchor line not found in {PROVE_CI}: {after_line}")
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")

def _ensure_bounded_sorted_unique_block(text: str, begin: str, end: str, item_line: str) -> str:
    if begin not in text or end not in text:
        raise SystemExit(f"missing required markers: {begin} / {end}")

    pre, rest = text.split(begin, 1)
    mid, post = rest.split(end, 1)

    existing_lines = [ln.rstrip("\n") for ln in mid.splitlines()]
    kept = [ln.strip() for ln in existing_lines if ln.strip()]

    s = set(kept)
    s.add(item_line.strip())

    new_mid = "\n" + "\n".join(sorted(s)) + "\n"
    return pre + begin + new_mid + end + post

def main() -> None:
    changed = False

    prove_text = _read(PROVE_CI)
    prove_new = _insert_after_exact_line(prove_text, INSERT_AFTER_LINE, NEW_LINE)
    changed |= _write_if_changed(PROVE_CI, prove_new)

    idx_text = _read(OPS_INDEX)
    idx_new = _ensure_bounded_sorted_unique_block(idx_text, BEGIN_INDEX, END_INDEX, BULLET)
    changed |= _write_if_changed(OPS_INDEX, idx_new)

    if not changed:
        print("NOOP: already up to date")

if __name__ == "__main__":
    main()
