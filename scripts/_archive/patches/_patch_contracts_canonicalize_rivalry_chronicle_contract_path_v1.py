from __future__ import annotations

from pathlib import Path

OLD_DOC = "docs/contracts/rivalry_chronicle_contract_output_v1.md"
NEW_DOC = "docs/contracts/rivalry_chronicle_contract_output_v1.md"

OLD = Path(OLD_DOC)
NEW = Path(NEW_DOC)

# Restrict to text surfaces only (avoid docx/pdf/binaries).
REWRITE_GLOBS = (
    "docs/**/*.md",
    "scripts/**/*.sh",
    "scripts/**/*.py",
    "src/**/*.py",
)

def norm(s: str) -> str:
    return s.replace("\r\n", "\n")

def try_read_text(p: Path) -> str | None:
    try:
        return norm(p.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        # Skip non-utf8 files defensively (should be rare given glob restrictions).
        return None

def write_text(p: Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")

def tracked_paths(root: Path) -> list[Path]:
    out: list[Path] = []
    for g in REWRITE_GLOBS:
        out.extend(root.glob(g))
    return [p for p in out if p.is_file()]

def rewrite_in_file(p: Path, old: str, new: str) -> bool:
    s = try_read_text(p)
    if s is None or old not in s:
        return False
    write_text(p, s.replace(old, new))
    return True

def main() -> None:
    repo = Path(".").resolve()

    # (1) Ensure canonical doc name exists (idempotent)
    if NEW.exists():
        if OLD.exists():
            old_txt = try_read_text(OLD)
            new_txt = try_read_text(NEW)
            if old_txt is not None and new_txt is not None and old_txt == new_txt:
                OLD.unlink()
                print(f"OK: removed redundant duplicate {OLD_DOC}")
            else:
                print("WARN: OLD exists but differs or is non-utf8; leaving OLD in place")
        else:
            print("OK: canonical contract already present")
    else:
        if not OLD.exists():
            raise SystemExit(f"ERROR: expected {OLD_DOC} to exist")
        NEW.parent.mkdir(parents=True, exist_ok=True)
        old_txt = try_read_text(OLD)
        if old_txt is None:
            raise SystemExit(f"ERROR: cannot read {OLD_DOC} as utf-8")
        write_text(NEW, old_txt)
        OLD.unlink()
        print(f"OK: renamed {OLD_DOC} -> {NEW_DOC}")

    # (2) Rewrite references across text-only surfaces
    changed = 0
    for p in tracked_paths(repo):
        if p.resolve() == NEW.resolve():
            continue
        if rewrite_in_file(p, OLD_DOC, NEW_DOC):
            changed += 1

    print(f"OK: rewritten references in {changed} file(s)")

if __name__ == "__main__":
    main()
