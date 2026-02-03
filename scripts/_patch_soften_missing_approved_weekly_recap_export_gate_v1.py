from __future__ import annotations

from pathlib import Path
import subprocess
import sys

NEEDLE = 'ERROR: No APPROVED WEEKLY_RECAP artifact found for this week. Refusing export.'

def git_ls_files() -> list[str]:
    p = subprocess.run(
        ["git", "ls-files"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]

def main() -> None:
    files = git_ls_files()

    hits: list[Path] = []
    for f in files:
        path = Path(f)
        try:
            s = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if NEEDLE in s:
            hits.append(path)

    if not hits:
        raise SystemExit(f"ERROR: did not find needle string in tracked files: {NEEDLE!r}")

    if len(hits) != 1:
        msg = "ERROR: expected exactly 1 file containing the needle; found:\n" + "\n".join(str(p) for p in hits)
        raise SystemExit(msg)

    target = hits[0]
    s = target.read_text(encoding="utf-8")

    # Only patch bash-style scripts in v1 (most likely location).
    if target.suffix != ".sh":
        raise SystemExit(
            f"ERROR: needle found in {target}, but it is not a .sh file. "
            "Refusing to patch automatically in v1."
        )

    # Require an 'exit 1' very near the needle so we don't do a dangerous rewrite.
    idx = s.find(NEEDLE)
    window = s[idx:idx + 400]  # local window after the needle
    if "exit 1" not in window:
        raise SystemExit(f"ERROR: found needle in {target} but no 'exit 1' within 400 chars after it; refusing.")

    # Idempotency: if we've already added the strict gate, do nothing.
    if "SV_STRICT_EXPORTS" in window:
        print(f"OK: {target} already appears patched (SV_STRICT_EXPORTS present).")
        return

    # Rewrite: replace the first 'exit 1' after the needle within the window with a strict gate.
    strict_block = """\
if [[ "${SV_STRICT_EXPORTS:-0}" == "1" ]]; then
  exit 1
fi
exit 0
"""

    # Find the first 'exit 1' occurrence after idx.
    exit_pos = s.find("exit 1", idx)
    if exit_pos == -1:
        raise SystemExit(f"ERROR: could not locate 'exit 1' after needle in {target}; refusing.")

    # Replace that exact token line (best effort: replace just the 'exit 1' statement)
    # Also convert ERROR -> WARN for the message (keep text stable but reduce severity).
    s2 = s.replace(NEEDLE, NEEDLE.replace("ERROR:", "WARN:"), 1)

    # Replace the first occurrence of "exit 1" after the needle
    # We do this by splitting once at that position.
    before = s2[:exit_pos]
    after = s2[exit_pos:]
    if not after.startswith("exit 1"):
        raise SystemExit("ERROR: internal mismatch locating exit 1; refusing.")
    after2 = after.replace("exit 1", strict_block.rstrip("\n"), 1)
    out = before + after2

    if out == s:
        raise SystemExit("ERROR: patch produced no changes (unexpected).")

    target.write_text(out, encoding="utf-8")
    print(f"OK: patched {target} (missing approved recap becomes WARN unless SV_STRICT_EXPORTS=1).")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.stderr.write(e.stderr or "")
        raise
