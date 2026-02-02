#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/ops_orchestrate.sh")

OLD = r'''run_chain "pass1" "$@"

pass1_changed="0"
if changed_after_pass; then
  pass1_changed="1"
  summarize_changes
else
  echo "==> no changes"
fi

run_chain "pass2 (idempotency check)" "$@"

if changed_after_pass; then
  echo
  echo "==> status after pass2:"
  git status --porcelain >&2
  die "idempotency failure: patch chain produced changes on re-run"
fi
echo "==> idempotency OK (no changes on re-run)"
'''

NEW = r'''run_chain "pass1" "$@"

pass1_changed="0"
if changed_after_pass; then
  pass1_changed="1"
  summarize_changes
else
  echo "==> no changes"
fi

# Snapshot the diff state after pass1 for idempotency verification.
pass1_diff="$(git diff)"
pass1_diff_cached="$(git diff --cached)"

run_chain "pass2 (idempotency check)" "$@"

# Idempotency semantics: pass2 must not introduce *additional* changes.
pass2_diff="$(git diff)"
pass2_diff_cached="$(git diff --cached)"

if [[ "${pass2_diff}" != "${pass1_diff}" ]] || [[ "${pass2_diff_cached}" != "${pass1_diff_cached}" ]]; then
  echo
  echo "==> status after pass2:"
  git status --porcelain >&2
  die "idempotency failure: pass2 changed the diff state vs pass1"
fi
echo "==> idempotency OK (pass2 introduced no new changes)"
'''

def main() -> None:
    text = TARGET.read_text(encoding="utf-8")

    if NEW in text:
        print("OK: ops_orchestrate idempotency semantics already patched (v1).")
        return

    if OLD not in text:
        raise SystemExit("ERROR: could not locate expected idempotency block in scripts/ops_orchestrate.sh")

    TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print("OK: patched ops_orchestrate idempotency semantics (v1).")

if __name__ == "__main__":
    main()
