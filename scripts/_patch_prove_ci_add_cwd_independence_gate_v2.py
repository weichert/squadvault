from __future__ import annotations
from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

ANCHOR_CALL_SUBSTRINGS = [
    "gate_enforce_test_db_routing_v1.sh",
]

INSERT_BLOCK = """\
echo "=== Gate: CWD independence (shims) v1 ==="
repo_root_for_gate="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
bash "${repo_root_for_gate}/scripts/gate_cwd_independence_shims_v1.sh"
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"ERROR: missing {TARGET}")

    s = TARGET.read_text(encoding="utf-8")

    if "gate_cwd_independence_shims_v1.sh" in s:
        raise SystemExit(
            "ERROR: prove_ci.sh already references gate_cwd_independence_shims_v1.sh.\n"
            "Refusing to double-insert. Ensure prove_ci.sh is clean, then re-run."
        )

    anchor_pos = -1
    for needle in ANCHOR_CALL_SUBSTRINGS:
        anchor_pos = s.find(needle)
        if anchor_pos != -1:
            break

    if anchor_pos == -1:
        raise SystemExit(
            "ERROR: could not find DB routing gate call anchor in scripts/prove_ci.sh.\n"
            f"Searched for: {ANCHOR_CALL_SUBSTRINGS}\n"
            "Refusing to guess insertion point."
        )

    lines = s.splitlines(True)
    running = 0
    insert_idx = None
    for i, line in enumerate(lines):
        running += len(line)
        if running >= anchor_pos:
            insert_idx = i + 1
            break
    assert insert_idx is not None

    block = "\n" + INSERT_BLOCK + "\n"
    lines.insert(insert_idx, block)

    TARGET.write_text("".join(lines), encoding="utf-8")
    print("OK: inserted CWD gate (v2) after DB routing gate call.")

if __name__ == "__main__":
    main()
