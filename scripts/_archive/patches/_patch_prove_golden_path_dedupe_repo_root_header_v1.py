from __future__ import annotations

from pathlib import Path

F = Path("scripts/prove_golden_path.sh")

def _is_script_dir_line(s: str) -> bool:
    # Allow minor quoting variations.
    return s.startswith('SCRIPT_DIR="') and "BASH_SOURCE[0]" in s and "dirname" in s

def _is_repo_root_line(s: str) -> bool:
    return s.startswith('REPO_ROOT="') and "SCRIPT_DIR" in s and "/.." in s

def _is_cd_repo_root_line(s: str) -> bool:
    return s in ('cd "${REPO_ROOT}"', "cd '${REPO_ROOT}'", 'cd "$REPO_ROOT"', "cd '${REPO_ROOT}'", "cd ${REPO_ROOT}")

def main() -> None:
    if not F.exists():
        raise SystemExit(f"Missing {F}")

    lines = F.read_text(encoding="utf-8").splitlines(keepends=True)

    out: list[str] = []
    saw_primary_block = False
    removed = 0

    i = 0
    while i < len(lines):
        s = lines[i].strip()

        # Detect header block patterns: SCRIPT_DIR, REPO_ROOT, (optional cd REPO_ROOT)
        if _is_script_dir_line(s) and i + 1 < len(lines) and _is_repo_root_line(lines[i + 1].strip()):
            # Determine if this block includes cd "${REPO_ROOT}" on the next line
            has_cd = False
            if i + 2 < len(lines) and _is_cd_repo_root_line(lines[i + 2].strip()):
                has_cd = True

            if not saw_primary_block:
                # Keep the first occurrence (primary). Prefer the one that includes cd, but we
                # can't safely reorder here; we just keep the first block as primary.
                out.append(lines[i])
                out.append(lines[i + 1])
                if has_cd:
                    out.append(lines[i + 2])
                    i += 3
                else:
                    i += 2
                saw_primary_block = True
                continue

            # After primary block: remove duplicate block iff it is a plain duplicate header.
            # We remove SCRIPT_DIR + REPO_ROOT always, and also remove cd "${REPO_ROOT}" if present.
            removed += 1
            i += 3 if has_cd else 2

            # Also remove an immediately-following blank line (optional) to keep formatting tidy.
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            continue

        out.append(lines[i])
        i += 1

    if removed == 0:
        return  # idempotent no-op

    F.write_text("".join(out), encoding="utf-8")

if __name__ == "__main__":
    main()
