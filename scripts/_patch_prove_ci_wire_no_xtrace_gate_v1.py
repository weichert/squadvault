from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

SNIPPET = """\
echo "==> No-xtrace guardrail gate"
./scripts/gate_no_xtrace_v1.sh
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if "gate_no_xtrace_v1.sh" in txt:
        print("OK: no-xtrace gate already wired (no-op).")
        return

    lines = txt.splitlines(True)

    # Insert near other early static gates; prefer right after the "no bare chevron" gate label,
    # or failing that, after "OK: repo cleanliness (before)" line block doesn't exist here.
    insert_after_idx = None

    for i, ln in enumerate(lines):
        if "No-bare-chevron markers gate" in ln:
            insert_after_idx = i
            break

    # Fallback: after "== CI Proof Suite ==" banner
    if insert_after_idx is None:
        for i, ln in enumerate(lines):
            if ln.strip() == "== CI Proof Suite ==":
                insert_after_idx = i
                break

    if insert_after_idx is None:
        raise SystemExit("Refusing to patch: could not find a safe insertion anchor in scripts/prove_ci.sh")

    insertion = SNIPPET
    # Ensure a blank line before the inserted block for readability.
    out = "".join(lines[: insert_after_idx + 1]) + "\n" + insertion + "".join(lines[insert_after_idx + 1 :])

    TARGET.write_text(out, encoding="utf-8")
    print("OK: wired gate_no_xtrace_v1.sh into scripts/prove_ci.sh")

if __name__ == "__main__":
    main()
