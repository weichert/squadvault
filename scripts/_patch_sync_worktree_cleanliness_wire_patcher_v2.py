from __future__ import annotations

from pathlib import Path

WIRE = Path("scripts/_patch_prove_ci_wire_worktree_cleanliness_gate_v1.py")

CANON = r'''from __future__ import annotations

import re
from pathlib import Path

PROVE = Path("scripts/prove_ci.sh")

BEGIN_TOP = "# SV_GATE: worktree_cleanliness (v1) begin\n"
END_TOP = "# SV_GATE: worktree_cleanliness (v1) end\n"

WRAP_BEGIN = "# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin\n"
WRAP_END = "# SV_GATE: worktree_cleanliness_wrap_proof (v1) end\n"

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def strip_existing(text: str) -> str:
    # Retry-safe: remove prior inserted blocks so regeneration is deterministic.
    text = re.sub(
        re.escape(WRAP_BEGIN) + r".*?" + re.escape(WRAP_END),
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        re.escape(BEGIN_TOP) + r".*?" + re.escape(END_TOP),
        "",
        text,
        flags=re.DOTALL,
    )
    # Remove duplicated end-of-run call (best effort)
    text = re.sub(
        r"^\s*scripts/gate_worktree_cleanliness_v1\.sh end \"\$\{SV_WORKTREE_SNAP0\}\"\s*\n",
        "",
        text,
        flags=re.MULTILINE,
    )
    return text

def find_insert_after_provenance_or_strict(lines: list[str]) -> int:
    for i, line in enumerate(lines):
        if "prove_ci provenance" in line:
            return i + 1
    for i, line in enumerate(lines):
        if line.strip() == "set -euo pipefail":
            return i + 1
    die("could not find insertion point near strict-mode or provenance banner")

def already_wired(text: str) -> bool:
    # If wrapper markers exist, treat as already wired.
    return (WRAP_BEGIN in text and WRAP_END in text and "SV_WORKTREE_SNAP0" in text)

def main() -> None:
    if not PROVE.exists():
        die(f"missing {PROVE}")

    original = PROVE.read_text(encoding="utf-8")

    # If already wired, succeed without rewriting (idempotence / allowlist).
    if already_wired(original):
        return

    text = strip_existing(original)
    lines = text.splitlines(keepends=True)

    # 1) Entry snapshot + assert
    ins = find_insert_after_provenance_or_strict(lines)
    top_block = (
        f"{BEGIN_TOP}"
        "SV_WORKTREE_SNAP0=\"$(scripts/gate_worktree_cleanliness_v1.sh begin)\"\n"
        "scripts/gate_worktree_cleanliness_v1.sh assert \"${SV_WORKTREE_SNAP0}\" \"prove_ci entry\"\n"
        f"{END_TOP}"
    )
    lines.insert(ins, top_block)

    # 2) Wrap each explicit proof invocation line: bash ... scripts/prove_*.sh ...
    proof_call_re = re.compile(r'^(?P<indent>\s*)bash\s+(?P<arg>.+)$')

    def extract_proof_path(bash_arg: str) -> str | None:
        m = re.search(r'(?P<p>(?:["\'])?[^ \t"\']*scripts/prove_[^ \t"\']+\.sh(?:["\'])?)', bash_arg)
        if not m:
            return None
        p = m.group("p")
        if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
            p = p[1:-1]
        if p.endswith("scripts/prove_ci.sh") or p.endswith("/scripts/prove_ci.sh"):
            return None
        return p

    wrapped_any = 0
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = proof_call_re.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        bash_arg = m.group("arg")
        proof_path = extract_proof_path(bash_arg)
        if proof_path is None:
            out.append(line)
            i += 1
            continue

        indent = m.group("indent")
        invocation = line

        block = (
            f"{indent}{WRAP_BEGIN}"
            f"{indent}SV_WORKTREE_SNAP_PROOF=\"$(scripts/gate_worktree_cleanliness_v1.sh begin)\"\n"
            f"{invocation}"
            f"{indent}scripts/gate_worktree_cleanliness_v1.sh assert \"${{SV_WORKTREE_SNAP_PROOF}}\" \"after {proof_path}\"\n"
            f"{indent}{WRAP_END}"
        )
        out.append(block)
        wrapped_any += 1
        i += 1

    # If we couldn't find proof invocations but we DID add the entry block, we must fail closed
    # unless we can detect that the repo's proof suite isn't expressed as bash prove_*.sh lines.
    #
    # In this repo, once the wiring has been applied, we should have already returned via already_wired().
    if wrapped_any == 0:
        die("no explicit proof invocations matched (expected bash ... scripts/prove_*.sh ...)")

    # 3) End-of-run assertion
    end_call = "scripts/gate_worktree_cleanliness_v1.sh end \"${SV_WORKTREE_SNAP0}\"\n"
    joined = "".join(out)
    if end_call not in joined:
        inserted = False
        final: list[str] = []
        for line in out:
            if (not inserted) and ("repo cleanliness (after)" in line):
                final.append(end_call)
                inserted = True
            final.append(line)
        if not inserted:
            final.append("\n")
            final.append(end_call)
        out = final

    PROVE.write_text("".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
'''

def main() -> None:
    if WIRE.exists() and WIRE.read_text(encoding="utf-8") == CANON:
        return
    WIRE.write_text(CANON, encoding="utf-8")

if __name__ == "__main__":
    main()
