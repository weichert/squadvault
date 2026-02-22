from __future__ import annotations

from pathlib import Path
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


def main() -> int:
    root = _repo_root()
    idx_rel = "docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
    idx = root / idx_rel
    if not idx.exists():
        raise SystemExit(f"ERROR: missing {idx_rel}")

    begin = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->"
    end = "<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->"

    s = _read(idx)
    if begin not in s or end not in s:
        raise SystemExit("ERROR: bounded markers not found in CI_Guardrails_Index_v1.0.md")

    pre, rest = s.split(begin, 1)
    mid, post = rest.split(end, 1)

    gate_path = "scripts/gate_pytest_tracked_tests_only_v1.sh"
    canonical = f"- {gate_path} — Pytest must only target tracked Tests/ paths (v1)\n"

    lines = mid.splitlines(keepends=True)

    # Remove any line that mentions the gate path but is not the canonical bullet.
    new_lines = []
    for ln in lines:
        if gate_path in ln and ln != canonical:
            continue
        new_lines.append(ln)

    # Ensure canonical bullet exists exactly once
    if canonical not in new_lines:
        # Insert among "- scripts/..." bullets, keeping lexicographic order on the script path.
        script_bullets = []
        other_lines = []

        for ln in new_lines:
            if ln.startswith("- scripts/") and " — " in ln:
                script_bullets.append(ln)
            else:
                other_lines.append(ln)

        script_bullets.append(canonical)

        def key_fn(ln: str) -> str:
            # "- scripts/foo.sh — desc"
            try:
                return ln.split(" — ", 1)[0]
            except Exception:
                return ln

        script_bullets = sorted(script_bullets, key=key_fn)

        # Rebuild: keep non-script lines in original order, but place script bullets
        # where the first script bullet originally appeared; otherwise append at end.
        first_script_idx = None
        for i, ln in enumerate(new_lines):
            if ln.startswith("- scripts/") and " — " in ln:
                first_script_idx = i
                break

        rebuilt = []
        if first_script_idx is None:
            rebuilt = new_lines
            if not rebuilt or not rebuilt[-1].endswith("\n"):
                rebuilt.append("\n")
            rebuilt.extend(script_bullets)
        else:
            # walk original lines; when we hit first script bullet, dump the whole sorted list once
            emitted = False
            for ln in new_lines:
                if (not emitted) and ln.startswith("- scripts/") and " — " in ln:
                    rebuilt.extend(script_bullets)
                    emitted = True
                    continue
                if emitted and ln.startswith("- scripts/") and " — " in ln:
                    continue
                rebuilt.append(ln)

        new_lines = rebuilt

    out_mid = "".join(new_lines)
    out = pre + begin + out_mid + end + post

    if out == s:
        print("OK: CI Guardrails index already canonical for pytest-tracked-tests-only entry (noop).")
        return 0

    _clipwrite(idx_rel, out)
    print("OK: canonicalized CI Guardrails index entry for pytest-tracked-tests-only gate (v1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
