from __future__ import annotations

import re
import sys
from pathlib import Path

CANONICAL = "out"

TARGET = Path("scripts/gen_creative_surface_fingerprint_v1.py")

SCOPE_MARKER = "SV_CREATIVE_SURFACE_SCOPE_V1"

SCOPE_BLOCK = f"""
# {SCOPE_MARKER}
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
    p = p.replace("\\\\", "/")

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
""".lstrip("\n")


def _die(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_if_changed(path: Path, new: str) -> bool:
    old = _read(path)
    if old == new:
        return False
    path.write_text(new, encoding="utf-8", newline="\n")
    return True


def _insert_scope_block(s: str) -> str:
    if SCOPE_MARKER in s:
        return CANONICAL

    lines = s.splitlines(True)

    # Insert after last contiguous import statement block; else at top.
    import_end = None
    for i, line in enumerate(lines):
        if re.match(r"^(from\s+\S+\s+import\s+.+|import\s+\S+)", line.strip()):
            import_end = i

    if import_end is None:
        insert_at = 0
    else:
        insert_at = import_end + 1
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1

    lines.insert(insert_at, "\n" + SCOPE_BLOCK + "\n")
    return "".join(lines)


def _patch_shape_a_inline_lsfiles_splitlines(s: str) -> str | None:
    # Shape A:
    #   paths = ... ls-files ... splitlines()
    pattern = re.compile(
        r"(?P<lhs>^[ \t]*[A-Za-z_][A-Za-z0-9_]*[ \t]*=[ \t]*)(?P<rhs>.*ls-files.*?splitlines\(\)[^\n]*$)",
        re.MULTILINE,
    )
    m = pattern.search(s)
    if not m:
        return None

    lhs = m.group("lhs")
    rhs = m.group("rhs")
    replacement = lhs + "sorted(p for p in " + rhs + " if _sv_is_allowed_creative_surface_path_v1(p))"
    return s[: m.start()] + replacement + s[m.end() :]


def _patch_shape_b_consumer_assignment(s: str) -> str | None:
    # Shape B (your repo):
    #   files = _git_ls_files()
    # Patch to:
    #   files = sorted(p for p in _git_ls_files() if _sv_is_allowed_creative_surface_path_v1(p))
    pattern = re.compile(
        r"^(?P<indent>[ \t]*)(?P<var>[A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*_git_ls_files\(\)[ \t]*$",
        re.MULTILINE,
    )
    m = pattern.search(s)
    if not m:
        return None

    indent = m.group("indent")
    var = m.group("var")

    replacement = (
        f"{indent}{var} = sorted(p for p in _git_ls_files() "
        f"if _sv_is_allowed_creative_surface_path_v1(p))"
    )
    return s[: m.start()] + replacement + s[m.end() :]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    target = repo_root / TARGET

    if not target.exists():
        _die(f"missing target generator: {TARGET}")

    s = _read(target)

    # Already canonical?
    if SCOPE_MARKER in s and "_sv_is_allowed_creative_surface_path_v1" in s:
        # Also require that we actually apply the filter somewhere
        if "_sv_is_allowed_creative_surface_path_v1" in s and "sorted(p for p in _git_ls_files()" in s:
            print(f"OK: {TARGET}: already canonical ({SCOPE_MARKER})")
            return 0
        if re.search(r"_sv_is_allowed_creative_surface_path_v1\(p\)", s) and re.search(r"sorted\(p for p in .*splitlines\(\)", s):
            print(f"OK: {TARGET}: already canonical ({SCOPE_MARKER})")
            return 0
        # Marker exists but application missing → continue patching.

    if "ls-files" not in s and "_git_ls_files" not in s:
        _die(f"{TARGET}: expected 'ls-files' or _git_ls_files in generator but not found")

    s2 = _insert_scope_block(s)
    if s2 == CANONICAL:
        s2 = s

    # Try patch shapes in a deterministic order: B first (your current structure), then A.
    s3 = _patch_shape_b_consumer_assignment(s2)
    if s3 is None:
        s3 = _patch_shape_a_inline_lsfiles_splitlines(s2)

    if s3 is None:
        _die("could not find a known patch target (consumer _git_ls_files assignment or inline ls-files splitlines)")

    # Sanity: ensure marker + allowlist function exist and are used
    if SCOPE_MARKER not in s3:
        _die("scope marker missing after patch; refusing")
    if "_sv_is_allowed_creative_surface_path_v1" not in s3:
        _die("allowlist function missing after patch; refusing")
    if "_sv_is_allowed_creative_surface_path_v1(p)" not in s3:
        _die("allowlist not applied to any path; refusing")

    changed = _write_if_changed(target, s3)
    if not changed:
        print(f"OK: {TARGET}: no changes needed")
        return 0

    print(f"OK: patched creative surface fingerprint scope: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
