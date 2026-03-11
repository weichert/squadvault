from __future__ import annotations

from pathlib import Path

GATE = Path("scripts/gate_contract_surface_completeness_v1.sh")
PROVE = Path("scripts/prove_contract_surface_completeness_v1.sh")


GATE_TEXT = """\
#!/usr/bin/env bash
set -euo pipefail

# Contract Surface Completeness Gate (v1)
#
# Invariant:
# For every contract doc in docs/contracts/*_contract_*_v*.md
# - Must contain "## Enforced By" section
# - Must list >=1 enforcement surface (scripts/*.sh; gate_*/prove_* only; NOT run_*)
# - Every listed script must exist and contain exact markers:
#     # SV_CONTRACT_NAME: <expected>
#     # SV_CONTRACT_DOC_PATH: <doc path>
# - Reverse check: if any enforcement surface script declares this doc via markers,
#   it must be listed in the doc (no stale/missing entries; set equality).
#
# Deterministic, static scan only. Bash3-safe.

die() {
  echo "ERROR: $*" 1>&2
  exit 1
}

note() {
  echo "==> $*" 1>&2
}

trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf "%s" "$s"
}

derive_contract_name_from_filename() {
  local doc="$1"
  local base
  base="$(basename "$doc")"
  base="${base%.md}"

  local up
  up="$(printf "%s" "$base" | tr '[:lower:]' '[:upper:]' | sed -e 's/[^A-Z0-9]/_/g')"
  up="$(printf "%s" "$up" | sed -e 's/__*/_/g')"
  up="$(printf "%s" "$up" | sed -e 's/^_\\+//' -e 's/_\\+$//')"

  printf "%s" "$up"
}

read_contract_name_from_doc_or_derive() {
  local doc="$1"

  local line
  line="$(grep -n '^# SV_CONTRACT_NAME:' "$doc" | head -n 1 || true)"
  if [[ -n "$line" ]]; then
    local val
    val="$(printf "%s" "$line" | sed -e 's/^.*# SV_CONTRACT_NAME:[[:space:]]*//')"
    val="$(trim "$val")"
    if [[ -z "$val" ]]; then
      die "Empty SV_CONTRACT_NAME marker in doc: $doc"
    fi
    printf "%s" "$val"
    return 0
  fi

  derive_contract_name_from_filename "$doc"
}

collect_docs() {
  find docs/contracts -maxdepth 1 -type f -name "*_contract_*_v*.md" | LC_ALL=C sort
}

is_enforcement_surface_path() {
  local p="$1"
  [[ "$p" == scripts/gate_*".sh" ]] || [[ "$p" == scripts/prove_*".sh" ]]
}

reject_run_star() {
  local p="$1"
  [[ "$p" == scripts/run_* ]] && return 0 || return 1
}

extract_enforced_by_list() {
  local doc="$1"

  local start
  start="$(grep -n '^##[[:space:]]\\+Enforced By[[:space:]]*$' "$doc" | head -n 1 | cut -d: -f1 || true)"
  if [[ -z "$start" ]]; then
    die "Missing required section '## Enforced By' in contract doc: $doc"
  fi

  local after="$((start + 1))"

  awk -v start="$after" 'NR>=start {
    if ($0 ~ /^##[[:space:]]+/) exit 0
    print
  }' "$doc" \
    | sed -n -E 's/^[[:space:]]*-[[:space:]]*`(scripts\/[^`]+\.sh)`[[:space:]]*$/\1/p; s/^[[:space:]]*-[[:space:]]*(scripts\/[^[:space:]]+\.sh)[[:space:]]*$/\1/p' \
    | LC_ALL=C sort -u
}

file_contains_exact_marker() {
  local file="$1"
  local marker="$2"
  grep -Fqx "$marker" "$file"
}

validate_script_markers() {
  local script="$1"
  local expected_name="$2"
  local doc="$3"

  local m_name="# SV_CONTRACT_NAME: ${expected_name}"
  local m_doc="# SV_CONTRACT_DOC_PATH: ${doc}"

  file_contains_exact_marker "$script" "$m_name" || die "Marker mismatch: ${script} missing exact line: ${m_name}"
  file_contains_exact_marker "$script" "$m_doc" || die "Marker mismatch: ${script} missing exact line: ${m_doc}"
}

reverse_scan_declared_surfaces_for_doc() {
  local doc="$1"
  local m_doc="# SV_CONTRACT_DOC_PATH: ${doc}"

  grep -R -n -F -- "$m_doc" scripts \
    | cut -d: -f1 \
    | LC_ALL=C sort -u \
    | while IFS= read -r f; do
        [[ "$f" == scripts/*.sh ]] || continue
        if is_enforcement_surface_path "$f"; then
          if reject_run_star "$f"; then
            die "Forbidden: enforcement entry points to run_* script: $f (doc: $doc)"
          fi
          printf "%s\\n" "$f"
        else
          die "Non-enforcement script declares contract doc via SV_CONTRACT_DOC_PATH: $f (doc: $doc). Only gate_*/prove_* allowed."
        fi
      done
}

compare_sets_or_die() {
  local doc="$1"
  local labelA="$2"
  local a_file="$3"
  local labelB="$4"
  local b_file="$5"

  local diff
  diff="$(LC_ALL=C diff -u "$a_file" "$b_file" || true)"
  if [[ -n "$diff" ]]; then
    echo "ERROR: Contract surface mismatch for doc: $doc" 1>&2
    echo "ERROR: ${labelA} must exactly match ${labelB} (set equality)." 1>&2
    echo "$diff" 1>&2
    exit 1
  fi
}

main() {
  local docs
  docs="$(collect_docs || true)"
  if [[ -z "$docs" ]]; then
    note "No contract docs found under docs/contracts matching '*_contract_*_v*.md' (nothing to do)."
    exit 0
  fi

  local tmpdir
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  local doc
  while IFS= read -r doc; do
    [[ -n "$doc" ]] || continue
    [[ -f "$doc" ]] || die "Contract doc listed by find does not exist: $doc"

    local expected_name
    expected_name="$(read_contract_name_from_doc_or_derive "$doc")"
    [[ -n "$expected_name" ]] || die "Could not determine expected contract name for doc: $doc"

    local enforced_list_file="$tmpdir/enforced_by.list"
    extract_enforced_by_list "$doc" > "$enforced_list_file"

    if [[ ! -s "$enforced_list_file" ]]; then
      die "Empty Enforced By list in contract doc: $doc"
    fi

    while IFS= read -r script; do
      [[ -n "$script" ]] || continue

      [[ "$script" == scripts/* ]] || die "Enforced By entry must start with scripts/: doc=$doc entry=$script"
      [[ "$script" == *.sh ]] || die "Enforced By entry must end with .sh: doc=$doc entry=$script"

      if reject_run_star "$script"; then
        die "Enforced By entry must not reference scripts/run_*: doc=$doc entry=$script"
      fi

      [[ -f "$script" ]] || die "Enforced By script does not exist: doc=$doc entry=$script"
      is_enforcement_surface_path "$script" || die "Enforced By entry is not an enforcement surface (gate_*/prove_* only): doc=$doc entry=$script"

      validate_script_markers "$script" "$expected_name" "$doc"
    done < "$enforced_list_file"

    local reverse_list_file="$tmpdir/reverse.list"
    reverse_scan_declared_surfaces_for_doc "$doc" > "$reverse_list_file" || true

    if [[ ! -s "$reverse_list_file" ]]; then
      die "No enforcement surfaces declare SV_CONTRACT_DOC_PATH for doc: $doc (expected at least one). Ensure gate/prove scripts include markers."
    fi

    while IFS= read -r script; do
      [[ -n "$script" ]] || continue
      validate_script_markers "$script" "$expected_name" "$doc"
    done < "$reverse_list_file"

    LC_ALL=C sort -u "$enforced_list_file" > "$tmpdir/enforced.sorted"
    LC_ALL=C sort -u "$reverse_list_file" > "$tmpdir/reverse.sorted"

    compare_sets_or_die "$doc" "Enforced By (doc)" "$tmpdir/enforced.sorted" "Declared by scripts (repo)" "$tmpdir/reverse.sorted"
  done <<< "$docs"

  note "OK: Contract surface completeness (v1)"
}

main "$@"
"""

PROVE_TEXT = """\
#!/usr/bin/env bash
set -euo pipefail

echo "==> Proof: contract surface completeness gate (v1)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

bash scripts/gate_contract_surface_completeness_v1.sh

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: Proof mutated repo or left working tree dirty." 1>&2
  git status --porcelain=v1 1>&2
  exit 1
fi

echo "OK"
"""


def write_if_changed(path: Path, content: str) -> None:
  if path.exists():
    existing = path.read_text(encoding="utf-8")
    if existing == content:
      return
  path.write_text(content, encoding="utf-8")


def main() -> None:
  write_if_changed(GATE, GATE_TEXT)
  write_if_changed(PROVE, PROVE_TEXT)


if __name__ == "__main__":
  main()
