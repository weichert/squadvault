from __future__ import annotations

from pathlib import Path
import re

PROVE = Path("scripts/prove_ci.sh")
IDX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

GATE = "scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh"
GATE_ECHO = '=== Gate: prove_ci uses relative scripts invocations (v1) ==='
GATE_LINE = f"bash {GATE}"

BEGIN = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
END   = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

BULLET = "- scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh — Enforce prove_ci invokes scripts via relative paths (no $REPO_ROOT/absolute) (v1)"

def _write_if_changed(p: Path, new: str, old: str, label: str) -> None:
    if new == old:
        print(f"OK: {label} already canonical (noop)")
        return
    p.write_text(new, encoding="utf-8")
    print(f"OK: {label} patched")

def patch_prove() -> None:
    text = PROVE.read_text(encoding="utf-8")

    if GATE in text:
        _write_if_changed(PROVE, text, text, "prove_ci wiring")
        return

    # Insert near other late “sanity” gates; prefer after the no-double-scripts-prefix gate marker if present.
    anchor = "Gate: no double scripts prefix"
    idx = text.find(anchor)
    if idx != -1:
        line_end = text.find("\n", idx)
        ins = line_end + 1 if line_end != -1 else len(text)
    else:
        # fallback: append near end before unit tests banner if present
        m = re.search(r"^==> unit tests\b", text, flags=re.M)
        ins = m.start() if m else len(text)

    block = f'\necho "{GATE_ECHO}"\n{GATE_LINE}\n'
    new = text[:ins] + block + text[ins:]
    _write_if_changed(PROVE, new, text, "prove_ci wiring")

def patch_index() -> None:
    text = IDX.read_text(encoding="utf-8")

    b_ct = text.count(BEGIN)
    e_ct = text.count(END)
    if b_ct != 1 or e_ct != 1:
        raise SystemExit(f"ERR: expected exactly one bounded entrypoints block: BEGIN={b_ct} END={e_ct}")

    if BULLET in text:
        _write_if_changed(IDX, text, text, "Ops entrypoints index")
        return

    b_i = text.find(BEGIN)
    e_i = text.find(END)
    if not (0 <= b_i < e_i):
        raise SystemExit("ERR: entrypoints markers out of order")

    before = text[:e_i]
    after = text[e_i:]

    if not before.endswith("\n"):
        before += "\n"

    new = before + BULLET + "\n" + after
    _write_if_changed(IDX, new, text, "Ops entrypoints index")

def main() -> None:
    patch_prove()
    patch_index()

if __name__ == "__main__":
    main()
