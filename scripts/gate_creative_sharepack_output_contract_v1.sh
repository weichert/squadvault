#!/usr/bin/env bash
set -euo pipefail

# CWD independence: anchor repo root from this script's location (no git required).
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
cd "${repo_root}"

echo "=== Gate: creative sharepack output contract (v1) ==="

league_id="${SV_LEAGUE_ID:-${LEAGUE_ID:-${SQUADVAULT_LEAGUE_ID:-}}}"
season="${SV_SEASON:-${SEASON:-${SQUADVAULT_SEASON:-}}}"
week_index="${SV_WEEK_INDEX:-${WEEK_INDEX:-${SQUADVAULT_WEEK_INDEX:-}}}"

if [[ -z "${league_id}" || -z "${season}" || -z "${week_index}" ]]; then
  echo "ERROR: missing required env inputs for gate."
  echo "Set SV_LEAGUE_ID (or LEAGUE_ID), SV_SEASON (or SEASON), SV_WEEK_INDEX (or WEEK_INDEX)."
  exit 1
fi

if ! [[ "${season}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: season must be an integer, got: ${season}"
  exit 1
fi

if ! [[ "${week_index}" =~ ^[0-9]+$ ]]; then
  echo "ERROR: week_index must be an integer, got: ${week_index}"
  exit 1
fi

if (( week_index < 0 || week_index > 99 )); then
  echo "ERROR: week_index out of range 0..99: ${week_index}"
  exit 1
fi

week_dir="week_$(printf '%02d' "${week_index}")"
root="artifacts/creative/${league_id}/${season}/${week_dir}/sharepack_v1"

if [[ ! -d "${root}" ]]; then
  echo "ERROR: sharepack root missing: ${root}"
  echo "Hint: run generator first:"
  echo "  ./scripts/py scripts/gen_creative_sharepack_v1.py --league-id \"${league_id}\" --season \"${season}\" --week-index \"${week_index}\""
  exit 1
fi

required_files=(
  "README.md"
  "memes_caption_set_v1.md"
  "commentary_short_v1.md"
  "stats_fun_facts_v1.md"
  "manifest_v1.json"
)

echo "==> [1] Required files present"
for f in "${required_files[@]}"; do
  if [[ ! -f "${root}/${f}" ]]; then
    echo "ERROR: missing required file: ${root}/${f}"
    exit 1
  fi
done

echo "==> [2] No extra files (only required files allowed)"

tmp_a="$(mktemp)"
tmp_e="$(mktemp)"
trap 'rm -f "$tmp_a" "$tmp_e"' EXIT

(cd "${root}" && find . -type f -print | sed -E 's|^\./||' | LC_ALL=C sort) >"$tmp_a"
(printf "%s\n" "${required_files[@]}" | LC_ALL=C sort) >"$tmp_e"

if ! diff -u "$tmp_e" "$tmp_a" >/dev/null; then
  echo "ERROR: unexpected files under sharepack root (or missing files)."
  echo "Diff expected vs actual:"
  diff -u "$tmp_e" "$tmp_a" || true
  exit 1
fi

echo "==> [3] Validate manifest matches bytes + sha256"
ROOT_PATH="${root}" python - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

root = os.environ.get("ROOT_PATH")
if not root:
    raise SystemExit("ERROR: ROOT_PATH env not set")
rootp = Path(root)

manifest_path = rootp / "manifest_v1.json"
data = json.loads(manifest_path.read_text(encoding="utf-8"))

if data.get("version") != "v1":
    raise SystemExit("ERROR: manifest version must be 'v1'")
if data.get("root") != "sharepack_v1":
    raise SystemExit("ERROR: manifest root must be 'sharepack_v1'")

files = data.get("files")
if not isinstance(files, list):
    raise SystemExit("ERROR: manifest files must be a list")

seen_paths: list[str] = []
for entry in files:
    if not isinstance(entry, dict):
        raise SystemExit("ERROR: manifest file entries must be objects")
    path = entry.get("path")
    sha256 = entry.get("sha256")
    bsz = entry.get("bytes")
    if not isinstance(path, str) or not path:
        raise SystemExit("ERROR: manifest entry missing path")
    if not isinstance(sha256, str) or len(sha256) != 64:
        raise SystemExit(f"ERROR: manifest entry sha256 invalid for {path}")
    if not isinstance(bsz, int) or bsz < 0:
        raise SystemExit(f"ERROR: manifest entry bytes invalid for {path}")
    seen_paths.append(path)

required = {"README.md", "memes_caption_set_v1.md", "commentary_short_v1.md", "stats_fun_facts_v1.md"}
if set(seen_paths) != required:
    raise SystemExit(f"ERROR: manifest files set mismatch. expected={sorted(required)} actual={sorted(set(seen_paths))}")

if seen_paths != sorted(seen_paths):
    raise SystemExit("ERROR: manifest files not sorted lexicographically by path")

for path in seen_paths:
    p = rootp / path
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    size = len(b)
    ent = next(e for e in files if e["path"] == path)
    if ent["sha256"] != h:
        raise SystemExit(f"ERROR: sha256 mismatch for {path}")
    if ent["bytes"] != size:
        raise SystemExit(f"ERROR: bytes mismatch for {path}")

print("OK: manifest validated")
PY

echo "OK"
