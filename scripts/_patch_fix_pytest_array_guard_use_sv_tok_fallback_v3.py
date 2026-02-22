from __future__ import annotations

from pathlib import Path
import re
import stat
import subprocess


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _clipwrite(rel_path: str, content: str) -> None:
    root = _repo_root()
    proc = subprocess.run(
        ["bash", str(root / "scripts" / "clipwrite.sh"), rel_path],
        input=content,
        text=True,
        cwd=str(root),
    )
    if proc.returncode != 0:
        raise SystemExit(f"ERROR: clipwrite failed for {rel_path} (exit {proc.returncode}).")


def _chmod_x(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


MARKER = "SV_ALLOW_PYTEST_ARRAY_EXPANSION_TARGETS_v1"

# Quote-tolerant array expansion matcher:
#   ${gp_tests[@]}
#   "${gp_tests[@]}"
#   '${gp_tests[@]}'
#   '"${gp_tests[@]}"'
ARRAY_RE = r"^['\"]*\$\{[A-Za-z0-9_]+_tests\[@\]\}['\"]*$"

# Old guard forms we’ve injected previously (t-based):
OLD_GUARD_IF_RE = re.compile(
    r'''^(\s*)if \[ -n "\$\{t-\}" \ ] && echo "\$\{t-\}" \| grep -Eq\s+''',
)

# Also catch earlier unsafe form (if it still exists anywhere):
OLD_GUARD_IF_UNSAFE_RE = re.compile(
    r'''^(\s*)if echo "\$t" \| grep -Eq\s+''',
)

SV_TOK_LINE = 'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"\n'


def _upgrade_guards_in_shell(rel: str) -> bool:
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    if MARKER not in s:
        _chmod_x(p)
        print(f"OK: {rel} has no {MARKER} marker (noop).")
        return False

    # Idempotence: if we already have sv_tok fallback, we’re done.
    if 'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"' in s:
        _chmod_x(p)
        print(f"OK: {rel} already uses sv_tok fallback (noop).")
        return False

    lines = s.splitlines(keepends=True)
    out: list[str] = []
    changed = False

    i = 0
    while i < len(lines):
        ln = lines[i]

        # If we see the marker comment, we will ensure the next guard uses sv_tok.
        if MARKER in ln:
            out.append(ln)
            i += 1

            # After marker, we expect some comment lines, then an if-line.
            # We will insert SV_TOK_LINE right before the first if-line we see
            # *within the next ~10 lines*, and rewrite that if-line to reference sv_tok.
            inserted_sv_tok = False
            looked = 0
            while i < len(lines) and looked < 12:
                ln2 = lines[i]

                m_safe = OLD_GUARD_IF_RE.match(ln2)
                m_unsafe = OLD_GUARD_IF_UNSAFE_RE.match(ln2)

                if m_safe:
                    indent = m_safe.group(1)
                    if not inserted_sv_tok:
                        out.append(indent + SV_TOK_LINE)
                        inserted_sv_tok = True
                        changed = True
                    # Replace the if-line with a sv_tok-based, quote-tolerant, set -u safe variant.
                    out.append(
                        indent
                        + f'if [ -n "${{sv_tok-}}" ] && echo "${{sv_tok-}}" | grep -Eq \'{ARRAY_RE}\' ; then\n'
                    )
                    changed = True
                    i += 1
                    # copy the remainder of the guard block lines unchanged
                    # until we hit 'fi' (inclusive) or we bail after 12 lines.
                    while i < len(lines):
                        out.append(lines[i])
                        if lines[i].lstrip().startswith("fi"):
                            i += 1
                            break
                        i += 1
                    break

                if m_unsafe:
                    indent = m_unsafe.group(1)
                    if not inserted_sv_tok:
                        out.append(indent + SV_TOK_LINE)
                        inserted_sv_tok = True
                        changed = True
                    out.append(
                        indent
                        + f'if [ -n "${{sv_tok-}}" ] && echo "${{sv_tok-}}" | grep -Eq \'{ARRAY_RE}\' ; then\n'
                    )
                    changed = True
                    i += 1
                    while i < len(lines):
                        out.append(lines[i])
                        if lines[i].lstrip().startswith("fi"):
                            i += 1
                            break
                        i += 1
                    break

                out.append(ln2)
                i += 1
                looked += 1

            continue

        out.append(ln)
        i += 1

    if not changed:
        _chmod_x(p)
        print(f"OK: {rel} contained marker(s) but no upgradable guard lines were found (noop).")
        return False

    _clipwrite(rel, "".join(out))
    _chmod_x(p)
    print(f"OK: upgraded {rel} array-expansion guards to use sv_tok fallback (v3).")
    return True


def _upgrade_template_patcher(rel: str) -> bool:
    """Prevent future patch runs from re-injecting a t-only guard."""
    root = _repo_root()
    p = root / rel
    if not p.exists():
        raise SystemExit(f"ERROR: missing {rel}")

    s = _read(p)

    if MARKER not in s:
        print(f"OK: {rel} has no {MARKER} marker text (noop).")
        return False

    if 'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"' in s:
        print(f"OK: {rel} already emits sv_tok fallback (noop).")
        return False

    # Insert the sv_tok assignment immediately before the first guard 'if' that references t.
    # Then rewrite the if-line to sv_tok-based, quote-tolerant.
    s2 = s

    # 1) replace the canonical t-based safe line if present
    pat1 = r'if \[ -n "\$\{t-\}" \ ] && echo "\$\{t-\}" \| grep -Eq '
    if pat1 in s2:
        s2 = s2.replace(
            pat1,
            'sv_tok="${t-${tok-${arg-${target-${raw-}}}}}"\n'
            'if [ -n "${sv_tok-}" ] && echo "${sv_tok-}" | grep -Eq ',
            1,
        )

    # 2) ensure regex inside is quote-tolerant if still narrow
    s2 = s2.replace(
        r'\'^"?\$\{[A-Za-z0-9_]+_tests\[@\]\}"?$\'',
        r'\'^['"'"']*\$\{[A-Za-z0-9_]+_tests\[@\]\}['"'"']*$\'',
        1,
    )

    if s2 == s:
        print(f"OK: {rel} unchanged (noop).")
        return False

    _clipwrite(rel, s2)
    print(f"OK: updated {rel} to emit sv_tok fallback + quote-tolerant guard going forward (v3).")
    return True


def main() -> int:
    changed = False
    changed |= _upgrade_guards_in_shell("scripts/gate_pytest_tracked_tests_only_v1.sh")
    changed |= _upgrade_guards_in_shell("scripts/check_no_pytest_directory_invocation.sh")  # may noop
    changed |= _upgrade_template_patcher("scripts/_patch_fix_pytest_target_parser_allow_array_expansions_v1.py")

    if not changed:
        print("OK: no changes needed (noop).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
