from __future__ import annotations

from pathlib import Path
import re

PROVE = Path("scripts/prove_ci.sh")
GATE  = Path("scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh")

def _patch_prove_ci(text: str) -> str:
    # 1) Remove repo_root_for_gate absolute invocations (keep relative)
    text = text.replace(
        'bash "${repo_root_for_gate}/scripts/gate_creative_surface_registry_discoverability_v1.sh"',
        "bash scripts/gate_creative_surface_registry_discoverability_v1.sh",
    )

    # 2) Fix any literal "\n...bash scripts/... \n" embedded into a single shell line.
    # Example observed:
    #   echo "== Creative sharepack determinism (conditional) =="\nbash scripts/prove_ci_creative_sharepack_if_available_v1.sh\n
    text = re.sub(
        r'echo\s+"== Creative sharepack determinism \(conditional\) =="\s*\\n\s*bash\s+scripts/prove_ci_creative_sharepack_if_available_v1\.sh\s*\\n\s*',
        'echo "== Creative sharepack determinism (conditional) =="\\n'
        'bash scripts/prove_ci_creative_sharepack_if_available_v1.sh\\n',
        text,
        flags=re.M,
    )
    return text

def _patch_gate(text: str) -> str:
    # Replace the soft-structure checker with a more permissive one:
    # allow: if bash ..., VAR=... bash ..., VAR="..." bash ..., etc.
    begin = "# 3) Soft structure check:"
    end = 'done < "$PROVE"'

    i = text.find(begin)
    j = text.find(end)
    if i == -1 or j == -1 or not (i < j):
        raise SystemExit("ERR: expected soft-check block not found in gate script; refusing to guess")

    new_block = """# 3) Soft structure check: any bash-invoked scripts must ultimately call a relative scripts/*.sh
# Allow common prefixes:
#   - if bash scripts/...
#   - VAR=1 bash scripts/...
#   - VAR="x y" bash scripts/...
# Ignore comment lines.
while IFS= read -r line; do
  case "$line" in
    \\#*) continue ;;
  esac

  # Only inspect lines that mention a bash call to scripts/*.sh
  if ! echo "$line" | grep -Eq '[[:space:]]bash[[:space:]].*(\\./)?scripts/[^[:space:]"\\x27]+\\.sh'; then
    continue
  fi

  # Accept canonical relative patterns (with optional if + env assignments)
  if echo "$line" | grep -Eq '^[[:space:]]*(if[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*=("[^"]*"|\\x27[^\\x27]*\\x27|[^[:space:]]+)[[:space:]]+)*bash[[:space:]]+"?(\\./)?scripts/[^[:space:]"\\x27]+\\.sh"?([[:space:]]|$)'; then
    continue
  fi

  echo "ERR: non-canonical bash scripts invocation (must be relative):" >&2
  echo "  $line" >&2
  fail=1
done < "$PROVE\"\"\"

    new_text = text[:i] + new_block + "\n\n" + text[j:]
    return new_text

def _write_if_changed(p: Path, new: str, old: str, label: str) -> None:
    if new == old:
        print(f"OK: {label} already canonical (noop)")
        return
    p.write_text(new, encoding="utf-8")
    print(f"OK: {label} patched")

def main() -> None:
    prove_old = PROVE.read_text(encoding="utf-8")
    prove_new = _patch_prove_ci(prove_old)
    _write_if_changed(PROVE, prove_new, prove_old, "prove_ci normalization")

    gate_old = GATE.read_text(encoding="utf-8")
    gate_new = _patch_gate(gate_old)
    _write_if_changed(GATE, gate_new, gate_old, "relative-invocation gate soft-check")

if __name__ == "__main__":
    main()
