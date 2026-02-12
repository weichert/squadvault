from __future__ import annotations
from pathlib import Path

TARGET = Path("scripts/gate_creative_sharepack_output_contract_v1.sh")

GATE_TEXT = """#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "=== Gate: creative sharepack output contract (v1) ==="

league_id="${SV_LEAGUE_ID:-${LEAGUE_ID:-${SQUADVAULT_LEAGUE_ID:-}}}"
season="${SV_SEASON:-${SEASON:-${SQUADVAULT_SEASON:-}}}"
week_index="${SV_WEEK_INDEX:-${WEEK_INDEX:-${SQUADVAULT_WEEK_INDEX:-}}}"

if [[ -z "${league_id}" || -z "${season}" || -z "${week_index}" ]]; then
  echo "ERROR: missing required env inputs for gate."
  exit 1
fi

week_dir="week_$(printf '%02d' "${week_index}")"
root="artifacts/creative/${league_id}/${season}/${week_dir}/sharepack_v1"

if [[ ! -d "${root}" ]]; then
  echo "ERROR: sharepack root missing: ${root}"
  exit 1
fi

required_files=(
  "README.md"
  "memes_caption_set_v1.md"
  "commentary_short_v1.md"
  "stats_fun_facts_v1.md"
  "manifest_v1.json"
)

for f in "${required_files[@]}"; do
  if [[ ! -f "${root}/${f}" ]]; then
    echo "ERROR: missing required file: ${root}/${f}"
    exit 1
  fi
done

echo "OK"
"""

def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(GATE_TEXT, encoding="utf-8", newline="\n")
    print("OK")

if __name__ == "__main__":
    main()
