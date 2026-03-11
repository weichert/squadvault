from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/prove_ci.sh")

STAMP = """\
# ==> Provenance stamp (single-run, log self-identification)
# Prints commit/branch/cleanliness + key determinism env to make pasted logs auditable.
if command -v git >/dev/null 2>&1; then
  sv_commit="$(git rev-parse --short HEAD 2>/dev/null || echo UNKNOWN)"
  sv_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo UNKNOWN)"
  if [[ "${sv_branch}" == "HEAD" ]]; then sv_branch="DETACHED"; fi
  sv_clean="DIRTY"
  if [[ -z "$(git status --porcelain=v1 2>/dev/null)" ]]; then sv_clean="CLEAN"; fi
else
  sv_commit="NO_GIT"
  sv_branch="NO_GIT"
  sv_clean="UNKNOWN"
fi

echo "==> prove_ci provenance: commit=${sv_commit} branch=${sv_branch} repo=${sv_clean} TZ=${TZ:-} LC_ALL=${LC_ALL:-} LANG=${LANG:-}"
"""

def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    if "==> prove_ci provenance:" in txt or "Provenance stamp (single-run" in txt:
        print("OK: provenance stamp already present (no-op).")
        return

    lines = txt.splitlines(True)

    # Prefer inserting immediately after the locale/timezone determinism block we just added.
    anchor = "Determinism: pin locale + timezone"
    insert_after_idx: int | None = None

    for i, ln in enumerate(lines):
        if anchor in ln:
            # Insert after the 3 export lines following the anchor comment block.
            # We search forward for the last of LANG/LC_ALL/TZ exports.
            j = i
            last_export = None
            while j < len(lines):
                s = lines[j].strip()
                if s.startswith("export TZ=") or s.startswith("export LC_ALL=") or s.startswith("export LANG="):
                    last_export = j
                # Stop once we pass the block (first blank line after last export)
                if last_export is not None and j > last_export and s == "":
                    insert_after_idx = j
                    break
                j += 1
            if insert_after_idx is None and last_export is not None:
                insert_after_idx = last_export
            break

    # Fallback: after strict mode.
    if insert_after_idx is None:
        for i, ln in enumerate(lines):
            if ln.strip() == "set -euo pipefail":
                insert_after_idx = i
                break

    if insert_after_idx is None:
        raise SystemExit(
            "Refusing to patch: could not find a safe anchor "
            "(expected locale determinism block or 'set -euo pipefail') in scripts/prove_ci.sh"
        )

    insertion = "\n" + STAMP + "\n"
    out = "".join(lines[: insert_after_idx + 1]) + insertion + "".join(lines[insert_after_idx + 1 :])

    TARGET.write_text(out, encoding="utf-8")
    print("OK: patched scripts/prove_ci.sh with provenance stamp.")

if __name__ == "__main__":
    main()
