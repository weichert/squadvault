from __future__ import annotations

from pathlib import Path

PARSER = Path("scripts/_patch_ci_proof_surface_gate_parser_v2.py")
GATE = Path("scripts/check_ci_proof_surface_matches_registry_v1.sh")

# Old “anywhere in line” detector (too broad)
OLD_GATE = 'if [[ "${line}" == *scripts/prove_*\\.sh* ]]; then'
OLD_PARSER = 'if [[ "${line}" == *scripts/prove_*\\\\.sh* ]]; then'

# New detector: prove script must appear in invocation position
# (optional ENV assigns, optional bash, optional ./, then scripts/prove_*.sh, then space/EOL/backslash)
NEW_GATE = (
    'if [[ "${line}" =~ ^[[:space:]]*'
    '([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+)*'
    '((bash)[[:space:]]+)?'
    '(\\./)?'
    '(scripts/prove_[A-Za-z0-9_]+\\.sh)'
    '([[:space:]]|$|\\\\) ]]; then'
)

NEW_PARSER = (
    'if [[ "${line}" =~ ^[[:space:]]*'
    '([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]+[[:space:]]+)*'
    '((bash)[[:space:]]+)?'
    '(\\\\./)?'
    '(scripts/prove_[A-Za-z0-9_]+\\\\.sh)'
    '([[:space:]]|$|\\\\\\\\) ]]; then'
)

def die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")

def patch_file(path: Path, old: str, new: str) -> bool:
    if not path.exists():
        die(f"missing {path}")
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    return True

def main() -> None:
    changed_gate = patch_file(GATE, OLD_GATE, NEW_GATE)
    changed_parser = patch_file(PARSER, OLD_PARSER, NEW_PARSER)

    if not (changed_gate or changed_parser):
        die(
            "did not find expected OLD detector lines to replace.\n"
            "Check the exact 'if [[ \"${line}\" == *scripts/prove_*' line(s) and patch them directly."
        )

if __name__ == "__main__":
    main()
