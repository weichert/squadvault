from __future__ import annotations

from pathlib import Path
import sys

TARGET = Path("scripts/gate_ci_guardrails_registry_completeness_v1.sh")

NEW = """# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v3_BEGIN
awk '
  /^[[:space:]]*(#|$)/ { next }

  {
    line = $0

    if (match(line, /^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)="[^"]*scripts\\/gate_[^"]+\\.sh"/)) {
      decl = substr(line, RSTART, RLENGTH)
      var_name = decl
      sub(/^[[:space:]]*/, "", var_name)
      sub(/=.*/, "", var_name)

      value = decl
      sub(/^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*="/, "", value)
      sub(/"$/, "", value)
      sub(/^\\.\\//, "", value)
      sub(/^.*scripts\\//, "scripts/", value)

      vars[var_name] = value
      next
    }

    if (match(line, /^[[:space:]]*bash[[:space:]]+\\.\\/scripts\\/gate_[^[:space:];|&()]+\\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*bash[[:space:]]+/, "", path)
      sub(/[[:space:];|&()].*$/, "", path)
      sub(/^\\.\\//, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*bash[[:space:]]+scripts\\/gate_[^[:space:];|&()]+\\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*bash[[:space:]]+/, "", path)
      sub(/[[:space:];|&()].*$/, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*\\.\\/scripts\\/gate_[^[:space:];|&()]+\\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/[[:space:];|&()].*$/, "", path)
      sub(/^\\.\\//, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*scripts\\/gate_[^[:space:];|&()]+\\.sh([[:space:];|&()]|$)/)) {
      path = substr(line, RSTART, RLENGTH)
      sub(/[[:space:];|&()].*$/, "", path)
      print path
      next
    }

    if (match(line, /^[[:space:]]*bash[[:space:]]+"\\$[A-Za-z_][A-Za-z0-9_]*"([[:space:];|&()]|$)/)) {
      ref = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*bash[[:space:]]+"/, "", ref)
      sub(/".*$/, "", ref)
      sub(/^\\$/, "", ref)
      if (ref in vars) {
        print vars[ref]
      }
      next
    }

    if (match(line, /^[[:space:]]*"\\$[A-Za-z_][A-Za-z0-9_]*"([[:space:];|&()]|$)/)) {
      ref = substr(line, RSTART, RLENGTH)
      sub(/^[[:space:]]*"/, "", ref)
      sub(/".*$/, "", ref)
      sub(/^\\$/, "", ref)
      if (ref in vars) {
        print vars[ref]
      }
      next
    }
  }
' "$PROVE" \\
  | sort -u > "$executed"
# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v3_END
"""

def fail(msg: str) -> None:
    print("ERROR: " + msg, file=sys.stderr)
    raise SystemExit(1)

text = TARGET.read_text(encoding="utf-8")

markers = [
    (
        "# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v3_BEGIN",
        "# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v3_END",
    ),
    (
        "# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v2_BEGIN",
        "# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v2_END",
    ),
    (
        "# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v1_BEGIN",
        "# SV_PATCH: CI_GUARDRAIL_REGISTRY_EXECUTED_SURFACE_v1_END",
    ),
]

updated = None
for begin, end in markers:
    if begin in text or end in text:
        if begin not in text or end not in text:
            fail("executed-surface patch markers are unbalanced")
        start = text.index(begin)
        finish = text.index(end, start) + len(end)
        updated = text[:start] + NEW + text[finish:]
        break

if updated is None:
    fail("expected existing executed-surface patch block not found")

if updated == text:
    print("OK: no changes required")
    raise SystemExit(0)

TARGET.write_text(updated, encoding="utf-8")
print("OK: patched scripts/gate_ci_guardrails_registry_completeness_v1.sh")
