#!/usr/bin/env bash
set -euo pipefail

repo_root="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"

cd "${repo_root}"

fingerprint_file="${repo_root}/docs/80_indices/ops/CI_Guardrails_Surface_Fingerprint_v1.txt"
generator="${repo_root}/scripts/gen_ci_guardrails_surface_fingerprint_v1.py"

if [[ ! -f "${fingerprint_file}" ]]; then
  echo "ERROR: missing fingerprint file: ${fingerprint_file}" >&2
  exit 2
fi

if [[ ! -f "${generator}" ]]; then
  echo "ERROR: missing generator: ${generator}" >&2
  exit 2
fi

expected="$(tr -d '\r\n[:space:]' < "${fingerprint_file}")"
if [[ -z "${expected}" ]]; then
  echo "ERROR: empty fingerprint file: ${fingerprint_file}" >&2
  exit 2
fi

actual="$(
  PYTHONDONTWRITEBYTECODE=1 ./scripts/py - <<'PY'
import hashlib
import importlib.util
from pathlib import Path
import sys

repo = Path.cwd()
gen = repo / "scripts" / "gen_ci_guardrails_surface_fingerprint_v1.py"

spec = importlib.util.spec_from_file_location("sv_ci_guardrails_surface_fp", gen)
if spec is None or spec.loader is None:
    raise SystemExit(f"ERROR: could not load generator: {gen}")

mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

payload = mod.canonical_payload()
print(hashlib.sha256(payload.encode("utf-8")).hexdigest())
PY
)"

if [[ "${expected}" != "${actual}" ]]; then
  echo "CI GUARDRAIL FAILURE: guardrail surface drift detected" >&2
  echo "expected fingerprint: ${expected}" >&2
  echo "actual fingerprint: ${actual}" >&2
  exit 1
fi

echo "OK: CI guardrail surface freeze (v1)"
