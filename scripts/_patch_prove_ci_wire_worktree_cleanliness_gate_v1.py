from __future__ import annotations

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
    # Remove prior insertions to make patch retry-safe and idempotent.
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
        r"^\s*bash scripts/gate_worktree_cleanliness_v1\.sh end \"\$\{SV_WORKTREE_SNAP0\}\"\s*\n",
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

def main() -> None:
    if not PROVE.exists():
        die(f"missing {PROVE}")

    original = PROVE.read_text(encoding="utf-8")
    text = strip_existing(original)
    lines = text.splitlines(keepends=True)

    # 1) Entry snapshot+assert near provenance banner if present; else after strict mode.
    ins = find_insert_after_provenance_or_strict(lines)
    top_block = (
        f"{BEGIN_TOP}"
        "SV_WORKTREE_SNAP0=\"$(bash scripts/gate_worktree_cleanliness_v1.sh begin)\"\n"
        "bash scripts/gate_worktree_cleanliness_v1.sh assert \"${SV_WORKTREE_SNAP0}\" \"prove_ci entry\"\n"
        f"{END_TOP}"
    )
    lines.insert(ins, top_block)

    # 2) Wrap each explicit proof invocation.
    #
    # We match common patterns:
    #   bash scripts/prove_foo.sh
    #   bash "scripts/prove_foo.sh" ...
    #   bash ${SOMETHING}/scripts/prove_foo.sh ...
    #
    # We DO NOT touch:
    #   prove_ci.sh itself
    #   gate scripts
    #
    proof_call_re = re.compile(
        r'^(?P<indent>\s*)bash\s+(?P<arg>.+)$'
    )

    def extract_proof_path(bash_arg: str) -> str | None:
        # Try to find a token containing scripts/prove_*.sh (quoted or not).
        # Keep it conservative: first match wins.
        m = re.search(r'(?P<p>(?:["\'])?[^ \t"\']*scripts/prove_[^ \t"\']+\.sh(?:["\'])?)', bash_arg)
        if not m:
            return None
        p = m.group("p")
        # Strip quotes for label
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
        # Preserve the exact original invocation line (so we don't change behavior)
        invocation = line

        block = (
            f"{indent}{WRAP_BEGIN}"
            f"{indent}SV_WORKTREE_SNAP_PROOF=\"$(bash scripts/gate_worktree_cleanliness_v1.sh begin)\"\n"
            f"{invocation}"
            f"{indent}bash scripts/gate_worktree_cleanliness_v1.sh assert \"${{SV_WORKTREE_SNAP_PROOF}}\" \"after {proof_path}\"\n"
            f"{indent}{WRAP_END}"
        )
        out.append(block)
        wrapped_any += 1
        i += 1

    if wrapped_any == 0:
        die("no explicit proof invocations matched (expected bash ... scripts/prove_*.sh ...)")

    # 3) End-of-run assertion: prefer just before existing 'repo cleanliness (after)' banner if present.
    end_call = "bash scripts/gate_worktree_cleanliness_v1.sh end \"${SV_WORKTREE_SNAP0}\"\n"
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
