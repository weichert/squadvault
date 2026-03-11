from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

PROVE_CI = REPO_ROOT / "scripts" / "prove_ci.sh"
GATE_SH = REPO_ROOT / "scripts" / "gate_enforce_test_db_routing_v1.sh"
HELPER_PY = REPO_ROOT / "src" / "squadvault" / "testing" / "test_db.py"


@dataclass(frozen=True)
class ReplaceOnce:
    anchor: str
    insertion: str
    where: str  # "after" or "before"


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


def _insert_anchor_based(path: Path, rule: ReplaceOnce) -> None:
    s = _read_text(path)
    if rule.insertion.strip() in s:
        return  # idempotent

    idx = s.find(rule.anchor)
    if idx < 0:
        _fail(f"anchor not found in {path}: {rule.anchor!r}")

    if rule.where == "after":
        insert_at = idx + len(rule.anchor)
    elif rule.where == "before":
        insert_at = idx
    else:
        _fail(f"invalid rule.where: {rule.where}")

    out = s[:insert_at] + rule.insertion + s[insert_at:]
    path.write_text(out, encoding="utf-8")


def _glob_files(globs: list[str]) -> list[Path]:
    out: list[Path] = []
    for g in globs:
        out.extend(sorted(REPO_ROOT.glob(g)))
    return [p for p in out if p.is_file()]


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


def _ensure_gate_script() -> None:
    gate = """\
#!/usr/bin/env bash
set -euo pipefail

# Gate: Enforce canonical test DB routing (v1)

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

files="$(git ls-files 'Tests/**/*.py' 'tests/**/*.py' 2>/dev/null || true)"
if [[ -z "${files}" ]]; then
  exit 0
fi

violations=""
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  hits="$(grep -nF '.local_squadvault.sqlite' "$f" || true)"
  [[ -z "$hits" ]] && continue

  bad="$(printf '%s\\n' "$hits" \
    | grep -vF 'os.environ.get("SQUADVAULT_TEST_DB", ".local_squadvault.sqlite")' \
    | grep -vF "os.environ.get('SQUADVAULT_TEST_DB', '.local_squadvault.sqlite')" \
    || true)"

  if [[ -n "$bad" ]]; then
    violations+="${f}
${bad}

"
  fi
done <<< "$files"

if [[ -n "$violations" ]]; then
  echo "ERROR: forbidden test DB hardcoding detected." >&2
  echo "" >&2
  echo "Hard rule: tests must route DB paths via SQUADVAULT_TEST_DB (env.get default) or resolve_test_db()." >&2
  echo "" >&2
  echo "Offending files/lines:" >&2
  echo "" >&2
  printf '%s\\n' "$violations" >&2
  exit 1
fi
"""
    _write_text_if_changed(GATE_SH, gate, mode=0o755)


def _wire_gate_into_prove_ci() -> None:
    s = _read_text(PROVE_CI)

    export_anchor = "export SQUADVAULT_TEST_DB"
    banner_anchor = 'echo "== CI Proof Suite =="'

    insertion = """\


# Gate: enforce canonical test DB routing (v1)
bash scripts/gate_enforce_test_db_routing_v1.sh
"""

    if export_anchor in s:
        _insert_anchor_based(PROVE_CI, ReplaceOnce(export_anchor, insertion, "after"))
        return

    if banner_anchor in s:
        _insert_anchor_based(PROVE_CI, ReplaceOnce(banner_anchor, insertion, "after"))
        return

    _fail(
        "could not find a safe anchor in scripts/prove_ci.sh. "
        "Expected either 'export SQUADVAULT_TEST_DB' or 'echo \"== CI Proof Suite ==\"'."
    )


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


def main() -> None:
    _ensure_helper_module()
    _ensure_gate_script()
    _wire_gate_into_prove_ci()
    _safe_update_tests_if_present()
    print("OK: enforce canonical test DB routing (v1) applied")


if __name__ == "__main__":
    main()
