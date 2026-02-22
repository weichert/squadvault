from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess


REL = "scripts/gate_pytest_tracked_tests_only_v1.sh"
MARKER = "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1"
ANCHOR = "pytest target must start with Tests/"

# canonical sv_tok assignment: prefer first_path, then fall back to prior chain
SV_TOK_CANON = 'sv_tok="${first_path-${t-${tok-${arg-${target-${raw-}}}}}}"'


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel_path: str, content: str) -> None:
    root = _root()
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "clipwrite.sh"), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")


def _chmod_x(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# match a sv_tok assignment line we previously injected
SV_TOK_RE = re.compile(r'^\s*sv_tok="\$\{.*\}"\s*$')


def main() -> int:
    p = _root() / REL
    if not p.exists():
        raise SystemExit(f"ERROR: missing {REL}")

    s = _read(p)
    if MARKER not in s:
        raise SystemExit(f"ERROR: marker {MARKER} not found in {REL} (refusing).")
    if ANCHOR not in s:
        raise SystemExit(f"ERROR: anchor not found in {REL} (refusing).")

    lines = s.splitlines(keepends=True)
    out: list[str] = []
    changed = False

    i = 0
    while i < len(lines):
        ln = lines[i]

        # When we see the marker line, we’ll scan forward until the closing 'fi'
        # and ensure any sv_tok assignment in that guard is canonical.
        if MARKER in ln:
            out.append(ln)
            i += 1

            # keep comment lines immediately after marker
            while i < len(lines) and lines[i].lstrip().startswith("#") and MARKER not in lines[i]:
                out.append(lines[i])
                i += 1

            # now copy/patch through the closing fi
            while i < len(lines):
                cur = lines[i]
                # rewrite sv_tok assignment lines inside the guard
                if SV_TOK_RE.match(cur.rstrip("\n")):
                    indent = cur.split("s", 1)[0]  # preserve leading whitespace roughly
                    out.append(indent + SV_TOK_CANON + "\n")
                    changed = True
                    i += 1
                    continue

                out.append(cur)
                i += 1
                if cur.lstrip().startswith("fi"):
                    break
            continue

        out.append(ln)
        i += 1

    # Second pass (conservative): in case there are guard blocks near the anchor not under marker,
    # upgrade any sv_tok assignment in a small window above each anchor occurrence.
    text = "".join(out)
    lines2 = text.splitlines(keepends=True)
    out2: list[str] = []
    for idx, ln in enumerate(lines2):
        if ANCHOR in ln:
            win_start = max(0, idx - 25)
            # rewrite any sv_tok assignment in that window in-place
            for j in range(win_start, idx):
                if SV_TOK_RE.match(lines2[j].rstrip("\n")):
                    # mark for replacement by storing a sentinel; we’ll apply below
                    pass

        out2.append(ln)

    # Apply window upgrades by a simple global substitution only if the canonical line isn't already present.
    # This stays conservative: it only replaces sv_tok lines that *don't* already reference first_path.
    text2 = "".join(out)
    if SV_TOK_CANON not in text2:
        def repl(m: re.Match[str]) -> str:
            line = m.group(0)
            if "first_path" in line:
                return line
            # preserve indentation
            indent = line[: len(line) - len(line.lstrip())]
            return indent + SV_TOK_CANON

        text3 = re.sub(r'^[ \t]*sv_tok="\$\{.*\}"[ \t]*$', repl, text2, flags=re.MULTILINE)
        if text3 != text2:
            text2 = text3
            changed = True

    if not changed:
        _chmod_x(p)
        print("OK: sv_tok already prefers first_path everywhere relevant (noop).")
        return 0

    _clipwrite(REL, text2)
    _chmod_x(p)
    print("OK: updated sv_tok to prefer first_path for pytest array-expansion guard (v7).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
