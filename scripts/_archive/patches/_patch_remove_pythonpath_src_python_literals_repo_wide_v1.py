from __future__ import annotations

from pathlib import Path

TARGETS = [
    # Docs / operator guidance
    Path("docs/canonical/contracts/ops/Ops_Shim_and_CWD_Independence_Contract_v1.0.md"),
    # Operator UX strings
    Path("src/squadvault/consumers/recap_week_status.py"),
    # Ingest runner usage blocks
    Path("src/squadvault/ingest/franchises/_run_franchises_ingest.py"),
    Path("src/squadvault/ingest/players/_run_players_ingest.py"),
    # Patchers that contain the literal substring in replacement patterns / examples
    Path("scripts/_patch_examples_use_shims_v1.py"),
    Path("scripts/_patch_operator_scripts_use_shims_v1.py"),
    Path("scripts/_patch_lock_ops_shim_cwd_contract_v1.py"),
    Path("scripts/_patch_run_week6_writing_room_gate_use_shims.py"),
    Path("scripts/_patch_remove_literal_pythonpath_src_python_strings_v1.py"),
]

BAD = "PYTHONPATH=src " + "python"

def patch_text(path: Path, txt: str) -> str:
    # 1) Prefer shim invocation in user-facing guidance.
    # Replace common runnable forms.
    txt2 = txt.replace("PYTHONPATH=src " + "python -u ", "./scripts/py -u ")
    txt2 = txt2.replace("PYTHONPATH=src " + "python -m ", "./scripts/py -m ")
    txt2 = txt2.replace("PYTHONPATH=src " + "python ", "./scripts/py ")

    # 2) If any literal remains (docs/pachers), break the contiguous substring
    # without changing meaning where it's just being *mentioned*.
    # (Avoid introducing the exact substring again.)
    if BAD in txt2:
        txt2 = txt2.replace(BAD, "PYTHONPATH=src " + "python")

    return txt2

def main() -> None:
    touched = 0
    for p in TARGETS:
        if not p.exists():
            # Be strict only for expected repo paths
            raise SystemExit(f"ERROR: missing target: {p}")

        txt = p.read_text(encoding="utf-8")
        out = patch_text(p, txt)

        if out != txt:
            p.write_text(out, encoding="utf-8")
            print(f"OK: patched {p}")
            touched += 1

    if touched == 0:
        print("OK: no changes needed (no-op)")

if __name__ == "__main__":
    main()
