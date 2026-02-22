from __future__ import annotations

from pathlib import Path
import re
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel_path: str, content: str) -> None:
    root = _repo_root()
    clipwrite = root / "scripts" / "clipwrite.sh"
    proc = subprocess.run(
        ["bash", str(clipwrite), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")


def _find_autofill_source() -> Path:
    """
    Find the *source* file that emits:
      'unknown paths (add to DESC map)'
    It may be a python patcher invoked by a wrapper.
    """
    root = _repo_root()

    # Prefer git-tracked search (deterministic)
    proc = subprocess.run(
        ["bash", "-lc", "cd \"$1\" && git grep -n \"unknown paths (add to DESC map)\" -- scripts | head -n 1 | cut -d: -f1", "bash", str(root)],
        text=True,
        capture_output=True,
    )
    path = proc.stdout.strip()
    if path:
        p = root / path
        if p.exists():
            return p

    # Fallback: plain grep (if git grep misses for any reason)
    proc = subprocess.run(
        ["bash", "-lc", "cd \"$1\" && grep -RIl -- \"unknown paths (add to DESC map)\" scripts | head -n 1", "bash", str(root)],
        text=True,
        capture_output=True,
    )
    path = proc.stdout.strip()
    if not path:
        raise SystemExit("ERROR: could not locate autofill implementation emitting 'unknown paths (add to DESC map)'.")
    p = root / path
    if not p.exists():
        raise SystemExit(f"ERROR: located path does not exist: {p}")
    return p


_ENTRY_RE = re.compile(
    r'^(?P<indent>\s*)["\'](?P<key>scripts/[^"\']+)["\']\s*:\s*["\'](?P<val>[^"\']*)["\']\s*,?\s*$'
)


def _insert_mapping(src: str, key: str, val: str) -> str:
    """
    Heuristic:
    - Locate a contiguous block of '"scripts/...": "..."' entries (dict literal style)
      regardless of the variable name.
    - Insert key with same indent, keep keys sorted.
    """
    lines = src.splitlines(True)

    # Find first entry line
    first = None
    for i, ln in enumerate(lines):
        if _ENTRY_RE.match(ln.rstrip("\n")):
            first = i
            break
    if first is None:
        raise SystemExit("ERROR: could not find any '\"scripts/...\": \"...\"' mapping entries to patch.")

    # Find last contiguous entry line (stop when we leave the mapping block)
    last = first
    for j in range(first + 1, len(lines)):
        if _ENTRY_RE.match(lines[j].rstrip("\n")):
            last = j
            continue
        # allow blank lines inside block? no — keep block tight and deterministic
        break

    block = lines[first : last + 1]

    entries: dict[str, str] = {}
    indent = None
    for ln in block:
        m = _ENTRY_RE.match(ln.rstrip("\n"))
        if not m:
            raise SystemExit("ERROR: unexpected non-entry line inside mapping block; refusing.")
        indent = m.group("indent")
        entries[m.group("key")] = ln

    if key in entries:
        return src  # already present => NOOP

    if indent is None:
        indent = "    "

    entries[key] = f'{indent}"{key}": "{val}",\n'

    new_block = [entries[k] for k in sorted(entries.keys())]
    out_lines = lines[:first] + new_block + lines[last + 1 :]
    return "".join(out_lines)


def main() -> int:
    root = _repo_root()
    target = _find_autofill_source()
    s = _read(target)

    key = "scripts/gate_pytest_tracked_tests_only_v1.sh"
    val = "Pytest must only target tracked Tests/ paths (v1)"

    out = _insert_mapping(s, key=key, val=val)
    if out == s:
        print(f"OK: mapping already contains {key} (noop).")
        return 0

    _clipwrite(str(target.relative_to(root)), out)
    print(f"OK: added mapping entry for {key} in {target.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
