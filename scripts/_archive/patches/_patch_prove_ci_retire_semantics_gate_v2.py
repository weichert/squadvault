from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")
MARKER = "SV_PATCH_PROVE_CI_RETIRE_SEMANTICS_GATE_V2"

SNIPPET = r'''
# === Gate: retire semantics (v2) ===
# If the last commit message claims "retire", require that any removed patch scripts
# were archived under scripts/_retired/ in the same commit.
if git log -1 --pretty=%B | grep -qiE '\bretire(d)?\b'; then
  deleted_patch_scripts="$(git show --name-status --pretty="" HEAD | awk '$1=="D" && $2 ~ /^scripts\/(patch_|_patch_)/ {print $2}')"
  added_retired="$(git show --name-status --pretty="" HEAD | awk '$1=="A" && $2 ~ /^scripts\/_retired\// {print $2}')"
  if [[ -n "${deleted_patch_scripts}" && -z "${added_retired}" ]]; then
    echo "ERROR: retire semantics gate failed — commit message says retire, but deleted patch scripts without archiving under scripts/_retired/"
    echo "Deleted:"
    echo "${deleted_patch_scripts}" | sed 's/^/  - /'
    echo ""
    echo "Fix options:"
    echo "  - amend message (remove 'retire'), OR"
    echo "  - archive scripts under scripts/_retired/ in the same commit"
    exit 2
  fi
fi
# === End Gate: retire semantics (v2) ===
'''


def main() -> None:
    s = TARGET.read_text(encoding="utf-8")
    if MARKER in s:
        print(f"OK: {TARGET} already patched ({MARKER}).")
        return

    lines = s.splitlines(True)

    # Insert right after the "== CI Proof Suite ==" echo if present; else append near end.
    insert_i = None
    for i, line in enumerate(lines):
        if "== CI Proof Suite ==" in line:
            insert_i = i + 1
            break
    if insert_i is None:
        insert_i = len(lines)

    lines.insert(insert_i, f"\n# {MARKER}\n{SNIPPET}\n")
    TARGET.write_text("".join(lines), encoding="utf-8")
    print(f"OK: patched {TARGET} (retire semantics gate v2).")


if __name__ == "__main__":
    main()
