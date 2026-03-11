from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/check_filesystem_ordering_determinism.sh")
SENTINEL = "SV_PATCH: fs-order scan ignore __pycache__/ and *.pyc (portable v3)"

EXCLUDE_RE = r"(/__pycache__/|\.pyc$)"

GNU_FLAGS = [
    "--exclude-dir=__pycache__",
    "--exclude=*.pyc",
]

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def main() -> None:
    if not TARGET.exists():
        die(f"missing target: {TARGET}")

    txt = TARGET.read_text(encoding="utf-8")

    # 1) Remove GNU-only grep flags (BSD grep compatibility)
    stripped = txt
    for flag in GNU_FLAGS:
        stripped = stripped.replace(f" {flag}", "")
        stripped = stripped.replace(f"\t{flag}", "")
        stripped = stripped.replace(flag, "")

    # 2) Ensure we have an EXCLUDE_RE block near the top (idempotent)
    if SENTINEL not in stripped:
        lines = stripped.splitlines(True)
        out: list[str] = []
        inserted = False
        for i, ln in enumerate(lines):
            out.append(ln)
            if not inserted and i == 0 and ln.startswith("#!"):
                out.append("\n")
                out.append(f"# {SENTINEL}\n")
                out.append("# Portable exclusion: BSD grep lacks --exclude/--exclude-dir.\n")
                out.append(f"EXCLUDE_RE='{EXCLUDE_RE}'\n")
                out.append("# /SV_PATCH\n\n")
                inserted = True
        stripped = "".join(out)

    # 3) Apply EXCLUDE_RE filtering to common file-enumeration pipelines.
    #    We patch any line containing 'git ls-files' or 'find ' that is piped onward.
    changed = 0
    patched_lines: list[str] = []
    for ln in stripped.splitlines(True):
        ln2 = ln

        if ("git ls-files" in ln2) and ("grep -Ev \"$EXCLUDE_RE\"" not in ln2) and ("grep -Ev \"${EXCLUDE_RE}\"" not in ln2):
            if "|" in ln2:
                head, tail = ln2.split("|", 1)
                ln2 = f"{head}| grep -Ev \"$EXCLUDE_RE\" |{tail}"
                changed += 1

        if ("find " in ln2) and ("grep -Ev \"$EXCLUDE_RE\"" not in ln2) and ("grep -Ev \"${EXCLUDE_RE}\"" not in ln2):
            if "|" in ln2:
                head, tail = ln2.split("|", 1)
                ln2 = f"{head}| grep -Ev \"$EXCLUDE_RE\" |{tail}"
                changed += 1

        patched_lines.append(ln2)

    new_txt = "".join(patched_lines)

    # 4) Safety: refuse if we did nothing (means we didn't actually fix the pipeline)
    #    BUT: allow success if we only stripped GNU flags and sentinel already existed.
    did_strip = (new_txt != txt)
    did_filter = (changed > 0)
    has_sentinel = (SENTINEL in new_txt)

    if not did_strip and not did_filter and not has_sentinel:
        die("refusing to patch: no changes applied; gate structure not recognized")

    TARGET.write_text(new_txt, encoding="utf-8")
    print(f"OK: portable pyc/__pycache__ exclusion applied (pipeline patches={changed}; stripped_gnu={did_strip})")

if __name__ == "__main__":
    main()
