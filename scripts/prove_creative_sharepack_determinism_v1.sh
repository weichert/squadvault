#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

echo "=== Proof: creative sharepack determinism (v1) ==="

league_id="${SV_LEAGUE_ID:-${LEAGUE_ID:-${SQUADVAULT_LEAGUE_ID:-}}}"
season="${SV_SEASON:-${SEASON:-${SQUADVAULT_SEASON:-}}}"
week_index="${SV_WEEK_INDEX:-${WEEK_INDEX:-${SQUADVAULT_WEEK_INDEX:-}}}"

if [[ -z "${league_id}" || -z "${season}" || -z "${week_index}" ]]; then
  echo "ERROR: missing required env inputs for proof."
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
sharepack_root="artifacts/creative/${league_id}/${season}/${week_dir}/sharepack_v1"

work="$(mktemp -d)"
trap 'rm -rf "${work}"' EXIT

clean_sharepack() {
  if [[ -d "${sharepack_root}" ]]; then
    rm -rf "${sharepack_root}"
  fi
}

hash_tree() {
  local root="$1"
  if [[ ! -d "${root}" ]]; then
    echo "ERROR: missing dir to hash: ${root}" >&2
    exit 1
  fi

  (cd "${root}" && find . -type f -print | sed -E 's|^\./||' | LC_ALL=C sort) | while IFS= read -r rel; do
    sha="$(shasum -a 256 "${root}/${rel}" | awk '{print $1}')"
    bytes="$(wc -c < "${root}/${rel}" | tr -d ' ')"
    printf "%s  %s  %s\n" "${sha}" "${bytes}" "${rel}"
  done | shasum -a 256 | awk '{print $1}'
}

echo "==> [1] Run #1 (repo root): generate"
clean_sharepack
SV_LEAGUE_ID="${league_id}" SV_SEASON="${season}" SV_WEEK_INDEX="${week_index}"   ./scripts/py scripts/gen_creative_sharepack_v1.py --league-id "${league_id}" --season "${season}" --week-index "${week_index}"

echo "==> [2] Gate #1"
SV_LEAGUE_ID="${league_id}" SV_SEASON="${season}" SV_WEEK_INDEX="${week_index}"   bash scripts/gate_creative_sharepack_output_contract_v1.sh

echo "==> [3] Hash #1"
hash_a="$(hash_tree "${sharepack_root}")"
printf "%s\n" "${hash_a}" > "${work}/hash_a.txt"
echo "hash_a=${hash_a}"

echo "==> [4] Run #2 (non-repo CWD): regenerate"
clean_sharepack
cd "${work}"

SV_LEAGUE_ID="${league_id}" SV_SEASON="${season}" SV_WEEK_INDEX="${week_index}"   "${repo_root}/scripts/py" "${repo_root}/scripts/gen_creative_sharepack_v1.py" --league-id "${league_id}" --season "${season}" --week-index "${week_index}"

echo "==> [5] Gate #2"
SV_LEAGUE_ID="${league_id}" SV_SEASON="${season}" SV_WEEK_INDEX="${week_index}"   bash "${repo_root}/scripts/gate_creative_sharepack_output_contract_v1.sh"

echo "==> [6] Hash #2"
hash_b="$(hash_tree "${repo_root}/${sharepack_root}")"
printf "%s\n" "${hash_b}" > "${work}/hash_b.txt"
echo "hash_b=${hash_b}"

echo "==> [7] Compare"
diff -u "${work}/hash_a.txt" "${work}/hash_b.txt" >/dev/null || {
  echo "ERROR: determinism proof failed (hash mismatch)"
  diff -u "${work}/hash_a.txt" "${work}/hash_b.txt" || true
  exit 1
}

echo "OK"
