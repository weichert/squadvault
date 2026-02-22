from __future__ import annotations

import json
import subprocess
from pathlib import Path



# SV_CREATIVE_SURFACE_SCOPE_V1
#
# Creative Surface Fingerprint Scope (v1)
#
# Purpose:
# - Make the Creative Surface explicitly scope-controlled (NOT "all git ls-files").
# - Prevent unrelated tracked files (e.g., ops indices, tests, caches) from influencing the fingerprint.
#
# Include (allowlist):
# - scripts/gen_*
# - scripts/gate_creative_*
# - docs/contracts/creative_*
# - artifacts/exports/** (ONLY if git-tracked; runtime subpaths defensively excluded)
#
# Exclude (denylist, defensive):
# - docs/80_indices/**
# - **/__pycache__/** and *.pyc
# - tests/**, test/**, Testing/**
# - artifacts/exports/**/runtime/**, artifacts/exports/**/_runtime/**, artifacts/exports/**/tmp/**
#
# Determinism:
# - Normalize to POSIX-style strings.
# - Filter by allowlist/denylist.
# - Sort lexicographically.
#
# NOTE:
# - We still source from git-tracked inputs (`git ls-files`) but the allowlist is the authority.

def _sv_is_allowed_creative_surface_path_v1(p: str) -> bool:
    p = p.replace("\\", "/")

    # defensive excludes
    if "/__pycache__/" in p or p.endswith(".pyc"):
        return False
    if p.startswith("docs/80_indices/"):
        return False
    if p.startswith("tests/") or p.startswith("test/") or p.startswith("Testing/"):
        return False

    if p.startswith("artifacts/exports/"):
        if "/runtime/" in p or "/_runtime/" in p or "/tmp/" in p:
            return False
        return True

    # allowlist
    if p.startswith("scripts/gen_"):
        return True
    if p.startswith("scripts/gate_creative_"):
        return True
    if p.startswith("docs/contracts/creative_"):
        return True

    return False

OUT = Path("artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json")


def _git_ls_files() -> list[str]:
    p = subprocess.run(
        ["git", "ls-files"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    files = [line.strip() for line in p.stdout.splitlines() if line.strip()]
    files.sort()
    return files


def _read_prev_payload() -> dict:
    if not OUT.exists():
        return {}
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        # If artifact is malformed, fall back to empty to avoid crashing generator.
        return {}


def main() -> None:
    files = sorted(p for p in _git_ls_files() if _sv_is_allowed_creative_surface_path_v1(p))
    files_n = len(files)

    payload = _read_prev_payload()

    # Preserve schema keys: only mutate keys that already exist.
    if "files" in payload:
        payload["files"] = files
    if "files_n" in payload:
        payload["files_n"] = files_n

    OUT.parent.mkdir(parents=True, exist_ok=True)

    out_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if OUT.exists():
        cur = OUT.read_text(encoding="utf-8")
        if cur == out_text:
            print("OK: fingerprint already canonical (noop)")
            return

    OUT.write_text(out_text, encoding="utf-8")
    print(f"OK: wrote {OUT} (files={files_n})")


if __name__ == "__main__":
    main()
