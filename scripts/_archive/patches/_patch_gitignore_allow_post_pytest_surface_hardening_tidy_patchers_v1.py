from __future__ import annotations

from pathlib import Path

TARGET = Path(".gitignore")
HEADER = "# Canonical patchers (DO track these)"
ALLOWLINES = [
    "!scripts/_patch_gitignore_allow_post_pytest_surface_hardening_tidy_patchers_v1.py",
    "!scripts/_patch_docs_add_golden_path_pytest_pinning_index_v1.py",
    "!scripts/_patch_deprecate_obsolete_golden_path_patchers_v1.py",
    "!scripts/_patch_prove_golden_path_add_pinned_note_v1.py",
]

def main() -> None:
    if not TARGET.exists():
        raise SystemExit("ERROR: .gitignore not found")

    s = TARGET.read_text(encoding="utf-8")
    lines = s.splitlines(True)

    insert_at = None
    for i, line in enumerate(lines):
        if line.rstrip("\n") == HEADER:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit(f"ERROR: could not find header: {HEADER}")

    # Ensure each allowline exists exactly once.
    existing = set(l.rstrip("\n") for l in lines)
    to_add = [a for a in ALLOWLINES if a not in existing]
    if not to_add:
        return

    for a in reversed(to_add):
        lines.insert(insert_at, a + "\n")

    TARGET.write_text("".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
