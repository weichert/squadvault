#!/usr/bin/env bash
set -euo pipefail

# Gate: Enforce canonical test DB routing (v1)

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

files="$(git ls-files 'Tests/**/*.py' 'tests/**/*.py' 2>/dev/null || true)"
if [[ -z "${files}" ]]; then
  exit 0
fi

violations=""
while IFS= read -r f; do
  [[ -z "$f" ]] && continue
  hits="$(grep -nF '.local_squadvault.sqlite' "$f" || true)"
  [[ -z "$hits" ]] && continue

  bad="$(printf '%s\n' "$hits"     | grep -vF 'os.environ.get("SQUADVAULT_TEST_DB", ".local_squadvault.sqlite")'     | grep -vF "os.environ.get('SQUADVAULT_TEST_DB', '.local_squadvault.sqlite')"     || true)"

  if [[ -n "$bad" ]]; then
    violations+="${f}
${bad}

"
  fi
done <<< "$files"

if [[ -n "$violations" ]]; then
  echo "ERROR: forbidden test DB hardcoding detected." >&2
  echo "" >&2
  echo "Hard rule: tests must route DB paths via SQUADVAULT_TEST_DB (env.get default) or resolve_test_db()." >&2
  echo "" >&2
  echo "Offending files/lines:" >&2
  echo "" >&2
  printf '%s\n' "$violations" >&2
  exit 1
fi
