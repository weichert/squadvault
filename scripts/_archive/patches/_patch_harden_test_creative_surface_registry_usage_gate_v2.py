from __future__ import annotations

from pathlib import Path
import re

TEST = Path("Tests/test_creative_surface_registry_usage_gate_v1.py")

def main() -> None:
    if not TEST.exists():
        raise SystemExit(f"ERROR: missing test file: {TEST}")

    src = TEST.read_text(encoding="utf-8")

    # Idempotence marker
    if "test_gate_is_cwd_independent_and_never_flags_plumbing_tokens" in src:
        print("OK: test already hardened (noop)")
        return

    # Replace the whole file with a stricter, more correct invariant test.
    out = """\
from __future__ import annotations

from pathlib import Path
import os
import subprocess
import tempfile


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_gate(cwd: Path) -> subprocess.CompletedProcess[str]:
    repo = _repo_root()
    gate = repo / "scripts" / "gate_creative_surface_registry_usage_v1.sh"

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"

    return subprocess.run(
        ["bash", str(gate)],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )


def test_gate_is_cwd_independent_and_never_flags_plumbing_tokens() -> None:
    # This test is intentionally NOT "gate always passes".
    # It proves:
    #   (1) repo-root vs non-repo CWD produces the SAME outcome (CWD independence)
    #   (2) historical false-positive plumbing tokens never appear in output
    forbidden = {
        "CREATIVE_SURFACE_REGISTRY_ENTRIES",
        "CREATIVE_SURFACE_REGISTRY_ENTRY",
    }

    repo = _repo_root()

    p1 = _run_gate(repo)
    with tempfile.TemporaryDirectory(prefix="sv_gate_cwd_probe_") as td:
        p2 = _run_gate(Path(td))

    # CWD independence: same return code (pass/fail should not depend on cwd)
    assert p1.returncode == p2.returncode, (
        "gate returncode differs by cwd\\n"
        f"repo_root rc={p1.returncode}\\nstdout:\\n{p1.stdout}\\nstderr:\\n{p1.stderr}\\n"
        f"non_repo rc={p2.returncode}\\nstdout:\\n{p2.stdout}\\nstderr:\\n{p2.stderr}"
    )

    combined = "\\n".join([p1.stdout, p1.stderr, p2.stdout, p2.stderr])
    for tok in forbidden:
        assert tok not in combined, f"forbidden token surfaced in gate output: {tok}\\noutput:\\n{combined}"
"""
    TEST.write_text(out, encoding="utf-8")
    print("OK: hardened creative surface registry usage gate test (v2)")

if __name__ == "__main__":
    main()
