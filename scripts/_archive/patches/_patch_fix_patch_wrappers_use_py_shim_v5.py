from __future__ import annotations

import re
from pathlib import Path

WRAPPER_GLOB = "scripts/patch_*.sh"

# Ignore non-exec references
NON_EXEC_RE = re.compile(r'\b(cat\s+>\s+|test\s+-f\s+|-m\s+py_compile\b)')

# Any mention of a patcher token (optionally quoted, optionally repo_root-prefixed)
PATCHER_TOKEN_RE = re.compile(
    r'(?P<patcher>(?P<q>["\'])?(?:(?:\$\{?repo_root\}?|\$repo_root)/)?scripts/_patch_[A-Za-z0-9_]+\.py(?P=q)?)'
)

# Already-compliant shim launcher (broad + simple)
# Accept ./scripts/py, scripts/py, "$repo_root/scripts/py", "${repo_root}/scripts/py", or any */scripts/py
# Include ':' boundary because gate scans "file:line:content" strings.
ALREADY_SHIM_RE = re.compile(
    r'(^|[\s;:&(:])"?(?:'
    r'(?:\$\{?repo_root\}?|\$repo_root)/scripts/py'
    r'|\.?/scripts/py'
    r'|scripts/py'
    r'|[^"\s]*/scripts/py'
    r')"?($|[\s;:&)])'
)

def _unquote(tok: str) -> str:
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in ("'", '"'):
        return tok[1:-1]
    return tok

def _is_repo_root_style(patcher_tok: str) -> bool:
    p = _unquote(patcher_tok)
    return p.startswith("${repo_root}/") or p.startswith("$repo_root/")

# Launcher token (python-ish) that precedes the patcher token.
# IMPORTANT: catch "$python_bin" / "$python_exec" / "${python_bin}" / etc.
LAUNCHER_RE = re.compile(
    r'(^\s*)(?P<prefix>[^#\n]*?)'
    r'(?P<launcher>'
    r'\bpython3?\b'
    r'|\$\{PYTHON:-python\}|\$\{PYTHON:-python3\}'
    r'|\$\{?PYTHON[^ \t}]*\}?'
    r'|\$py|\$python'
    r'|\$\{py\}|\$\{python\}'
    r'|\$python_[A-Za-z0-9_]+'                # $python_bin, $python_exec, etc.
    r'|\$\{python_[A-Za-z0-9_]+\}'            # ${python_bin}, etc.
    r'|"\$py"|"\$python"'
    r'|"\$\{py\}"|"\$\{python\}"'
    r'|"\$python_[A-Za-z0-9_]+"'              # "$python_bin"
    r'|"\$\{python_[A-Za-z0-9_]+\}"'          # "${python_bin}"
    r'|"\$\{?PYTHON[^"]*\}"'
    r')'
    r'(?P<ws>\s+)'
    r'(?P<patcher>(?P<q>["\'])?(?:(?:\$\{?repo_root\}?|\$repo_root)/)?scripts/_patch_[A-Za-z0-9_]+\.py(?P=q)?)'
)

def rewrite_line(line: str) -> str:
    if re.match(r"^\s*#", line):
        return line
    if NON_EXEC_RE.search(line):
        return line
    if not PATCHER_TOKEN_RE.search(line):
        return line

    # Already shim? leave it.
    if ALREADY_SHIM_RE.search(line):
        return line

    m = LAUNCHER_RE.search(line)
    if not m:
        return line

    indent = m.group(1)
    prefix = m.group("prefix")
    ws = m.group("ws")
    patcher_tok = m.group("patcher")

    shim = '"${repo_root}/scripts/py"' if _is_repo_root_style(patcher_tok) else "./scripts/py"

    return indent + prefix + shim + ws + patcher_tok + line[m.end():]

def main() -> None:
    wrappers = sorted(Path(".").glob(WRAPPER_GLOB))
    if not wrappers:
        raise SystemExit("REFUSAL: no patch wrappers found")

    changed_files = 0
    for w in wrappers:
        src = w.read_text(encoding="utf-8").splitlines(keepends=True)
        out = []
        changed = False
        for line in src:
            new = rewrite_line(line)
            if new != line:
                changed = True
            out.append(new)
        if changed:
            w.write_text("".join(out), encoding="utf-8")
            changed_files += 1

    print(f"patched_wrappers={changed_files}")

if __name__ == "__main__":
    main()
