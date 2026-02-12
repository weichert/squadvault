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

    # Insert near top after deterministic env envelope confirmation (best-effort).
    anchor = 'echo "OK: deterministic env envelope"\n'
    if anchor in text:
        before, after = text.split(anchor, 1)
        before = before + anchor
    else:
        # Fallback: after set -euo pipefail line
        lines = text.splitlines(keepends=True)
        idx = None
        for k, ln in enumerate(lines):
            if ln.strip() == "set -euo pipefail":
                idx = k + 1
                break
        if idx is None:
            raise SystemExit("ERROR: could not find insertion point in prove_ci.sh")
        before = "".join(lines[:idx]) + "\n"
        after = "".join(lines[idx:])

    # Use scripts/py (shim-compliant). Avoid heredocs: use -c.
    block = (
        MARKER_BEGIN
        + 'sv_rt_start="$(./scripts/py -c \'import time; print(int(time.time()))\')"\n'
        + 'export SV_CI_RUNTIME_START_EPOCH_SECONDS="$sv_rt_start"\n'
        + "# SV_CI_PROOF_COUNT_EXPECTED may be set externally if desired.\n"
        + MARKER_END
    )

    end_anchor = 'echo "OK: worktree cleanliness (v1): end-of-run"\n'
    if end_anchor in after:
        pre2, post2 = after.split(end_anchor, 1)
        end_block = (
            end_anchor
            + 'sv_rt_end="$(./scripts/py -c \'import time; print(int(time.time()))\')"\n'
            + 'export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"\n'
            + "bash scripts/gate_ci_runtime_envelope_v1.sh\n"
        )
        after = pre2 + end_block + post2
    else:
        after = (
            after
            + "\n# SV_CI runtime envelope enforcement (best-effort; v1)\n"
            + 'sv_rt_end="$(./scripts/py -c \'import time; print(int(time.time()))\')"\n'
            + 'export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"\n'
            + "bash scripts/gate_ci_runtime_envelope_v1.sh\n"
        )

    PROVE.write_text(before + block + after, encoding="utf-8")
    print("OK: added runtime measurement exports + runtime envelope gate call (v1).")

if __name__ == "__main__":
    main()
