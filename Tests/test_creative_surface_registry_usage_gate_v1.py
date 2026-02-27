from __future__ import annotations

from pathlib import Path
import os
import subprocess
import tempfile


def _repo_root() -> Path:
    # Tests/ is at repo root; keep this simple + deterministic.
    return Path(__file__).resolve().parents[1]


def _run_gate(cwd: Path) -> subprocess.CompletedProcess[str]:
    repo = _repo_root()
    gate = repo / "scripts" / "gate_creative_surface_registry_usage_v1.sh"

    env = dict(os.environ)
    env["LC_ALL"] = "C"
    env["LANG"] = "C"

    # Use bash explicitly; gate is bash.
    return subprocess.run(
        ["bash", str(gate)],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )


def test_gate_passes_from_repo_root_and_non_repo_cwd() -> None:
    repo = _repo_root()

    # 1) Repo root CWD
    p1 = _run_gate(repo)
    assert p1.returncode == 0, f"gate failed from repo root\nstdout:\n{p1.stdout}\nstderr:\n{p1.stderr}"

    # 2) Non-repo CWD
    with tempfile.TemporaryDirectory(prefix="sv_gate_cwd_probe_") as td:
        p2 = _run_gate(Path(td))
        assert p2.returncode == 0, f"gate failed from non-repo cwd\nstdout:\n{p2.stdout}\nstderr:\n{p2.stderr}"


def test_gate_never_flags_registry_plumbing_tokens() -> None:
    # Historical false positives. If these show up again, something regressed in the scan/filter logic.
    forbidden = {
        "CREATIVE_SURFACE_REGISTRY_ENTRIES",
        "CREATIVE_SURFACE_REGISTRY_ENTRY",
    }

    repo = _repo_root()
    p = _run_gate(repo)

    # Even if the gate fails for a real reason in the future, we want to ensure these specific tokens
    # are never treated as missing surface IDs.
    combined = f"{p.stdout}\n{p.stderr}"
    for tok in forbidden:
        assert tok not in combined, f"forbidden token surfaced in gate output: {tok}\noutput:\n{combined}"
