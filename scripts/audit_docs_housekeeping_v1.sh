#!/usr/bin/env bash
set -euo pipefail
echo "=== Audit: docs housekeeping (v1) ==="

# Repo root
if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside a git repo" >&2
  exit 2
fi

# Ensure local audit dir exists (but never tracked)
mkdir -p .local_audit

# --- .gitignore hygiene ---
touch .gitignore

ensure_ignore_line() {
  local line="$1"
  if ! grep -qF -- "${line}" .gitignore; then
    echo "${line}" >> .gitignore
    echo "OK: .gitignore add: ${line}"
  fi
}

ensure_ignore_line ".DS_Store"
ensure_ignore_line ".local_audit/"

# --- Purge .DS_Store under docs ---
ds_count="$(find docs -type f -name '.DS_Store' -print 2>/dev/null | wc -l | tr -d ' ')"
if [ "${ds_count}" != "0" ]; then
  echo "Removing ${ds_count} .DS_Store files under docs/"
  find docs -type f -name '.DS_Store' -print -delete
else
  echo "OK: no .DS_Store under docs/"
fi

# --- Untrack .local_audit if it was committed (keep local files) ---
if git ls-files --error-unmatch .local_audit >/dev/null 2>&1; then
  echo "Untracking .local_audit/ (was committed)"
  git rm -r --cached .local_audit >/dev/null
else
  echo "OK: .local_audit not tracked"
fi

# --- Inventory snapshots ---
echo "Writing .local_audit/docs_ext_counts.txt"
find docs -type f 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -nr > .local_audit/docs_ext_counts.txt

echo "Writing .local_audit/docs_paths.txt"
find docs -type f -print 2>/dev/null | sort > .local_audit/docs_paths.txt

# --- Index / docmap candidates ---
echo "Writing .local_audit/docmap_candidates.txt"
find docs -type f 2>/dev/null | grep -i 'documentation_map\|docmap\|canonical\|index' | sort > .local_audit/docmap_candidates.txt

# --- Media / data files list ---
echo "Writing .local_audit/docs_media_data.txt"
find docs -type f \( -name '*.pdf' -o -name '*.png' -o -name '*.tsv' \) 2>/dev/null | sort > .local_audit/docs_media_data.txt

# --- Duplicate basename detection across extensions (python, no deps) ---
echo "Writing .local_audit/duplicate_basenames.txt"
python - <<'PY' > .local_audit/duplicate_basenames.txt
from pathlib import Path
from collections import defaultdict

root = Path("docs")
by_stem = defaultdict(list)

for p in root.rglob("*"):
    if p.is_file():
        by_stem[p.stem.lower()].append(p)

out = []
for stem, paths in by_stem.items():
    exts = {p.suffix.lower() for p in paths}
    if len(paths) > 1 and len(exts) > 1:
        out.append((stem, sorted(paths)))

for stem, paths in sorted(out):
    print(stem)
    for p in paths:
        print(f"  {p.as_posix()}")
    print()
PY

# --- Missing referenced docs/* paths (fail loud) ---
echo "Writing .local_audit/docs_path_mentions.txt"
grep -Roh --include='*.md' --include='*.txt' "docs/[A-Za-z0-9_./-]*" docs 2>/dev/null \
  | sort -u > .local_audit/docs_path_mentions.txt || true

echo "Writing .local_audit/missing_referenced_docs_paths.txt"
python - <<'PY' > .local_audit/missing_referenced_docs_paths.txt
from pathlib import Path

mentions = Path(".local_audit/docs_path_mentions.txt")
missing = []
if mentions.exists():
    for line in mentions.read_text().splitlines():
        s = line.strip()
        if not s:
            continue
        p = Path(s)
        if not p.exists():
            missing.append(s)

for m in missing:
    print(m)
PY

missing_count="$(wc -l < .local_audit/missing_referenced_docs_paths.txt | tr -d ' ')"
if [ "${missing_count}" != "0" ]; then
  echo
  echo "ERROR: ${missing_count} referenced docs/* paths are missing."
  echo "See: .local_audit/missing_referenced_docs_paths.txt"
  echo
  sed -n '1,120p' .local_audit/missing_referenced_docs_paths.txt || true
  exit 1
fi

echo "OK: no missing referenced docs/* paths."

echo
echo "=== Summary ==="
echo "ext counts:        .local_audit/docs_ext_counts.txt"
echo "docs paths:        .local_audit/docs_paths.txt"
echo "docmap candidates: .local_audit/docmap_candidates.txt"
echo "media/data list:   .local_audit/docs_media_data.txt"
echo "dupe basenames:    .local_audit/duplicate_basenames.txt"
echo "missing refs:      .local_audit/missing_referenced_docs_paths.txt"
echo "OK"
