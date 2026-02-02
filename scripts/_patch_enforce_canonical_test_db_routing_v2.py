from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

PROVE_CI = REPO_ROOT / "scripts" / "prove_ci.sh"
GATE_SH = REPO_ROOT / "scripts" / "gate_enforce_test_db_routing_v1.sh"
HELPER_PY = REPO_ROOT / "src" / "squadvault" / "testing" / "test_db.py"
GITIGNORE = REPO_ROOT / ".gitignore"

GATE_BLOCK_LINES = [
    "# Gate: enforce canonical test DB routing (v1)\n",
    "bash scripts/gate_enforce_test_db_routing_v1.sh\n",
]


@dataclass(frozen=True)
class ReplaceOnce:
    anchor_line: str
    insert_lines: list[str]
    where: str  # "after" only


def _fail(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def _read_text(p: Path) -> str:
    if not p.exists():
        _fail(f"missing required file: {p}")
    return p.read_text(encoding="utf-8")


def _write_text_if_changed(p: Path, content: str, mode: int | None = None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    existing = p.read_text(encoding="utf-8") if p.exists() else None
    if existing == content:
        return
    p.write_text(content, encoding="utf-8")
    if mode is not None:
        os.chmod(p, mode)


def _ensure_helper_module() -> None:
    helper = """\
\"\"\"SquadVault testing helpers (canonical).

Centralizes resolution of the canonical test DB path.

Hard invariant:
- Tests must not hardcode ".local_squadvault.sqlite" except via:
  os.environ.get("SQUADVAULT_TEST_DB", ".local_squadvault.sqlite")
  or resolve_test_db().
\"\"\"

from __future__ import annotations

import os


def resolve_test_db(default: str = ".local_squadvault.sqlite") -> str:
    v = os.environ.get("SQUADVAULT_TEST_DB")
    if v:
        return v
    return default
"""
    _write_text_if_changed(HELPER_PY, helper)


def _ensure_gate_script_exists() -> None:
    if GATE_SH.exists():
        return
    _fail(f"expected gate script to exist: {GATE_SH} (v2 patcher will not invent it)")


def _insert_gate_after_export_line() -> None:
    lines = Path(PROVE_CI).read_text(encoding="utf-8").splitlines(True)

    gate_block = "".join(GATE_BLOCK_LINES)
    if gate_block in "".join(lines):
        return  # already wired

    # Accept either export form:
    #   export SQUADVAULT_TEST_DB
    #   export SQUADVAULT_TEST_DB=...
    export_idx = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s == "export SQUADVAULT_TEST_DB" or s.startswith("export SQUADVAULT_TEST_DB="):
            export_idx = i
            break

    if export_idx is None:
        _fail("could not find export line 'export SQUADVAULT_TEST_DB' (line-based)")

    # Insert as whole lines (no substring replace)
    insert = ["\n"] + GATE_BLOCK_LINES + ["\n"]
    lines[export_idx + 1:export_idx + 1] = insert
    PROVE_CI.write_text("".join(lines), encoding="utf-8")


def _glob_files(globs: list[str]) -> list[Path]:
    out: list[Path] = []
    for g in globs:
        out.extend(sorted(REPO_ROOT.glob(g)))
    return [p for p in out if p.is_file()]


def _safe_update_tests_if_present() -> None:
    test_files = _glob_files(["Tests/**/*.py", "tests/**/*.py"])
    if not test_files:
        return

    literal = ".local_squadvault.sqlite"

    patterns = [
        (re.compile(rf'(\bsqlite3\.connect\()\s*["\']{re.escape(literal)}["\']\s*(\))'),
         r"\1resolve_test_db()\2"),
        (re.compile(rf'(\bconnect\()\s*["\']{re.escape(literal)}["\']\s*(\))'),
         r"\1resolve_test_db()\2"),
        (re.compile(rf'^(?P<indent>\s*)(?P<lhs>\w+\s*=\s*)["\']{re.escape(literal)}["\']\s*$'),
         r"\g<indent>\g<lhs>resolve_test_db()"),
    ]

    for p in test_files:
        txt = p.read_text(encoding="utf-8")
        if literal not in txt:
            continue

        if 'os.environ.get("SQUADVAULT_TEST_DB", ".local_squadvault.sqlite")' in txt:
            continue
        if "os.environ.get('SQUADVAULT_TEST_DB', '.local_squadvault.sqlite')" in txt:
            continue

        new = txt
        changed = False
        for rgx, repl in patterns:
            n2, count = rgx.subn(repl, new, flags=re.MULTILINE)
            if count:
                new = n2
                changed = True

        if not changed:
            continue

        if "from squadvault.testing.test_db import resolve_test_db" not in new:
            lines = new.splitlines(keepends=True)
            import_end = None
            for i, line in enumerate(lines):
                if line.startswith("#") or line.strip() == "":
                    continue
                if line.startswith("import ") or line.startswith("from "):
                    import_end = i
                    continue
                break
            if import_end is None:
                continue
            lines.insert(import_end + 1, "from squadvault.testing.test_db import resolve_test_db\n")
            new = "".join(lines)

        if new != txt:
            p.write_text(new, encoding="utf-8")


def _unignore_patchers_if_needed() -> None:
    if not GITIGNORE.exists():
        return
    s = _read_text(GITIGNORE)
    if "!scripts/_patch_*.py" in s:
        return
    # refuse-to-guess: only add if the ignore line exists as a full line
    lines = s.splitlines(True)
    for i, line in enumerate(lines):
        if line.rstrip("\n") == "scripts/_patch_*.py":
            lines.insert(i + 1, "!scripts/_patch_*.py\n")
            GITIGNORE.write_text("".join(lines), encoding="utf-8")
            return


def main() -> None:
    _ensure_helper_module()
    _ensure_gate_script_exists()
    _insert_gate_after_export_line()
    _safe_update_tests_if_present()
    _unignore_patchers_if_needed()
    print("OK: enforce canonical test DB routing (v2) applied")


if __name__ == "__main__":
    main()
