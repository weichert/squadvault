from __future__ import annotations

from pathlib import Path
import re

PROVE = Path("scripts/prove_ci.sh")
GATE  = Path("scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh")

def patch_prove(text: str) -> str:
    # 1) Absolute via repo_root_for_gate -> relative
    text = text.replace(
        'bash "${repo_root_for_gate}/scripts/gate_creative_surface_registry_discoverability_v1.sh"',
        "bash scripts/gate_creative_surface_registry_discoverability_v1.sh",
    )

    # 2) Fix the literal '\n...bash ...\n' that got embedded into a single line
    # (turn it into 2 real lines)
    text = text.replace(
        'echo "== Creative sharepack determinism (conditional) =="\\n'
        'bash scripts/prove_ci_creative_sharepack_if_available_v1.sh\\n',
        'echo "== Creative sharepack determinism (conditional) =="\\n'
        'bash scripts/prove_ci_creative_sharepack_if_available_v1.sh\\n',
    )

    # More robust: if the bad single-line form exists, split it
    text = re.sub(
        r'echo\s+"== Creative sharepack determinism \(conditional\) =="\\n\s*bash\s+scripts/prove_ci_creative_sharepack_if_available_v1\.sh\\n',
        'echo "== Creative sharepack determinism (conditional) =="\\n'
        'bash scripts/prove_ci_creative_sharepack_if_available_v1.sh\\n',
        text,
        flags=re.M,
    )
    return text

def patch_gate(text: str) -> str:
    # Replace section 3 to allow:
    #   if bash scripts/foo.sh ...
    #   VAR=1 bash scripts/foo.sh ...
    #   VAR="x y" bash scripts/foo.sh ...
    # and still forbid:
    #   bash "$REPO_ROOT/scripts/..."
    #   bash "/abs/.../scripts/..."
    #
    # We identify the section starting at "# 3) Soft structure check:" and ending at 'done < "$PROVE"'
    begin = "# 3) Soft structure check:"
    end = 'done < "$PROVE"'

    i = text.find(begin)
    j = text.find(end)
    if i == -1 or j == -1 or not (i < j):
        raise SystemExit("ERR: expected soft-check block not found in gate script; refusing to guess")

    lines = []
    lines.append("# 3) Soft structure check: bash-invoked scripts must be relative (scripts/*.sh).")
    lines.append("# Allow prefixes like: if ..., VAR=... , VAR=\"x y\" ...")
    lines.append("# Ignore comment lines.")
    lines.append('while IFS= read -r line; do')
    lines.append('  case "$line" in')
    lines.append('    \\#*) continue ;;')
    lines.append('  esac')
    lines.append('')
    lines.append('  # Only inspect lines that mention a bash call to scripts/*.sh')
    lines.append('  if ! echo "$line" | grep -Eq \'[[:space:]]bash[[:space:]].*(\\./)?scripts/[^[:space:]"\\x27]+\\.sh\'; then')
    lines.append('    continue')
    lines.append('  fi')
    lines.append('')
    lines.append('  # Accept canonical relative patterns (with optional if + env assignments)')
    lines.append('  if echo "$line" | grep -Eq \'^[[:space:]]*(if[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*=("[^"]*"|\\x27[^\\x27]*\\x27|[^[:space:]]+)[[:space:]]+)*bash[[:space:]]+"?(\\./)?scripts/[^[:space:]"\\x27]+\\.sh"?([[:space:]]|$)\'; then')
    lines.append('    continue')
    lines.append('  fi')
    lines.append('')
    lines.append('  echo "ERR: non-canonical bash scripts invocation (must be relative):" >&2')
    lines.append('  echo "  $line" >&2')
    lines.append('  fail=1')
    lines.append('done < "$PROVE"')

    new_block = "\n".join(lines)
    new_text = text[:i] + new_block + "\n\n" + text[j:]
    return new_text

def write_if_changed(p: Path, new: str, old: str, label: str) -> None:
    if new == old:
        print(f"OK: {label} already canonical (noop)")
        return
    p.write_text(new, encoding="utf-8")
    print(f"OK: {label} patched")

def main() -> None:
    prove_old = PROVE.read_text(encoding="utf-8")
    prove_new = patch_prove(prove_old)
    write_if_changed(PROVE, prove_new, prove_old, "prove_ci normalization")

    gate_old = GATE.read_text(encoding="utf-8")
    gate_new = patch_gate(gate_old)
    write_if_changed(GATE, gate_new, gate_old, "relative-invocation gate soft-check")

if __name__ == "__main__":
    main()
