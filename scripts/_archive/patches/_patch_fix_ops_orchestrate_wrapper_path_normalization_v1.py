#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path

TARGET = Path("scripts/ops_orchestrate.sh")

OLD = r'''    local wpath="$wrapper"
    if [[ "${wpath}" != /* ]]; then
      wpath="${REPO_ROOT}/${wpath}"
    fi
    [[ -f "${wpath}" ]] || die "patch wrapper not found: ${wrapper}"
    [[ -x "${wpath}" ]] || die "patch wrapper not executable: ${wrapper} (chmod +x required)"

    case "${wpath}" in
      "${REPO_ROOT}/scripts/"*) ;;
      *) die "wrapper is outside scripts/: ${wrapper}" ;;
    esac
'''

NEW = r'''    local wpath="$wrapper"
    if [[ "${wpath}" != /* ]]; then
      wpath="${REPO_ROOT}/${wpath}"
    fi

    # Canonicalize path to remove ./ and ../ (bash 3.2 safe)
    local wdir wbase
    wdir="$(cd "$(dirname "${wpath}")" && pwd)"
    wbase="$(basename "${wpath}")"
    wpath="${wdir}/${wbase}"

    [[ -f "${wpath}" ]] || die "patch wrapper not found: ${wrapper}"
    [[ -x "${wpath}" ]] || die "patch wrapper not executable: ${wrapper} (chmod +x required)"

    case "${wpath}" in
      "${REPO_ROOT}/scripts/"*) ;;
      *) die "wrapper is outside scripts/: ${wrapper}" ;;
    esac
'''

def main() -> None:
    text = TARGET.read_text(encoding="utf-8")
    if NEW in text:
        print("OK: ops_orchestrate already normalized (v1).")
        return
    if OLD not in text:
        raise SystemExit("ERROR: could not locate expected wrapper path block in scripts/ops_orchestrate.sh")
    TARGET.write_text(text.replace(OLD, NEW), encoding="utf-8")
    print("OK: patched scripts/ops_orchestrate.sh (v1).")

if __name__ == "__main__":
    main()
