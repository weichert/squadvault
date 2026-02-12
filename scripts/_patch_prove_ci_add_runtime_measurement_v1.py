from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVE = REPO_ROOT / "scripts" / "prove_ci.sh"

MARKER_BEGIN = "# --- SV_CI_RUNTIME_MEASUREMENT_v1_BEGIN ---\n"
MARKER_END   = "# --- SV_CI_RUNTIME_MEASUREMENT_v1_END ---\n"

def main() -> None:
    text = PROVE.read_text(encoding="utf-8")
    if MARKER_BEGIN in text and MARKER_END in text:
        print("OK: runtime measurement block already present (idempotent).")
        return

    # Insert near top after deterministic env/provenance banner (best-effort anchor).
    # We'll anchor on the first "OK: deterministic env envelope" echo if present; else after shebang+set.
    anchor = 'echo "OK: deterministic env envelope"\n'
    if anchor in text:
        pre, post = text.split(anchor, 1)
        insertion_point = anchor
        before = pre + insertion_point
        after = post
    else:
        # fallback: after first blank line following set -euo pipefail
        lines = text.splitlines(keepends=True)
        idx = 0
        for i, ln in enumerate(lines):
            if ln.strip() == "set -euo pipefail":
                idx = i + 1
                break
        before = "".join(lines[:idx]) + "\n"
        after = "".join(lines[idx:])

    block = (
        MARKER_BEGIN
        'sv_rt_start="$(python - <<\'PY\'\n'
        "import time\n"
        "print(int(time.time()))\n"
        "PY\n"
        ')"\n'
        "export SV_CI_RUNTIME_START_EPOCH_SECONDS=\"$sv_rt_start\"\n"
        "# SV_CI_PROOF_COUNT_EXPECTED may be set externally if desired.\n"
        MARKER_END
    )

    # Also ensure we export runtime at end: anchor near last cleanliness end-of-run line.
    end_anchor = 'echo "OK: worktree cleanliness (v1): end-of-run"\n'
    if end_anchor in after:
        pre2, post2 = after.split(end_anchor, 1)
        end_block = (
            end_anchor
            'sv_rt_end="$(python - <<\'PY\'\n'
            "import time\n"
            "print(int(time.time()))\n"
            "PY\n"
            ')"\n'
            'export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"\n'
            "bash scripts/gate_ci_runtime_envelope_v1.sh\n"
        )
        after = pre2 + end_block + post2
    else:
        # minimal: append to end (safe even if prove_ci exits earlier; still fine)
        after = (
            after
            + "\n# SV_CI runtime envelope enforcement (best-effort; v1)\n"
            + 'sv_rt_end="$(python - <<\'PY\'\nimport time\nprint(int(time.time()))\nPY\n)"\n'
            + 'export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"\n'
            + "bash scripts/gate_ci_runtime_envelope_v1.sh\n"
        )

    PROVE.write_text(before + block + after, encoding="utf-8")
    print("OK: added runtime measurement exports + runtime envelope gate call (v1).")

if __name__ == "__main__":
    main()
