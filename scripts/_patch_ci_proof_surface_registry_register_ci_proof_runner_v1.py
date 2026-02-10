from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REG = Path("docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md")

SURF_BEGIN = "<!-- SV_PROOF_SURFACE_LIST_v1_BEGIN -->"
SURF_END = "<!-- SV_PROOF_SURFACE_LIST_v1_END -->"

RUN_BEGIN = "<!-- CI_PROOF_RUNNERS_BEGIN -->"
RUN_END = "<!-- CI_PROOF_RUNNERS_END -->"

BULLET_RE = re.compile(r"^-\ (scripts/prove_[A-Za-z0-9_]+\.sh)\ —\ .+$")


@dataclass(frozen=True)
class Args:
    script: str
    desc: str


def die(msg: str) -> "NoReturn":
    raise SystemExit(msg)


def _get_args() -> Args:
    if len(sys.argv) != 3:
        die(
            "FAIL: usage:\n"
            "  scripts/patch_ci_proof_surface_registry_register_ci_proof_runner_v1.sh "
            "\"scripts/prove_xxx_v1.sh\" \"Description...\"\n"
            "Refusing to guess description (fail-closed)."
        )
    script = sys.argv[1].strip()
    desc = sys.argv[2].strip()

    if not script.startswith("scripts/prove_") or not script.endswith(".sh"):
        die(f"FAIL: script must be scripts/prove_*.sh; got: {script}")

    if "—" in desc:
        die("FAIL: description must not contain em-dash '—' (reserved delimiter).")

    if desc == "":
        die("FAIL: description is required (non-empty).")

    if len(desc) > 140:
        die("FAIL: description too long (max 140 chars).")

    return Args(script=script, desc=desc)


def _split_bounded(s: str, begin: str, end: str) -> tuple[str, str, str]:
    if begin not in s or end not in s:
        die(f"FAIL: missing bounded markers:\n  {begin}\n  {end}")
    before, rest = s.split(begin, 1)
    middle, after = rest.split(end, 1)
    return before, middle, after


def _canon_surface_list(middle: str, script: str) -> str:
    lines = [ln.strip() for ln in middle.splitlines() if ln.strip()]
    entry = f"- {script}"
    if entry not in lines:
        lines.append(entry)
    out = sorted(set(lines), key=lambda x: x)
    return "\n" + "\n".join(out) + "\n"


def _canon_ci_proof_runners(middle: str, script: str, desc: str) -> str:
    good = f"- {script} — {desc}"

    kept: list[str] = []
    bad_lines: list[str] = []

    for raw in middle.splitlines():
        t = raw.strip()
        if not t:
            continue
        if t.startswith("<!--") and t.endswith("-->"):
            continue

        if "scripts/prove_" in t and not BULLET_RE.match(t):
            bad_lines.append(t)
            continue

        if BULLET_RE.match(t):
            kept.append(t)
        else:
            bad_lines.append(t)

    if bad_lines:
        die(
            "FAIL: CI_PROOF_RUNNERS block contains nonconforming line(s). Refusing to proceed.\n"
            "Fix the block to only contain strict bullets:\n"
            "  - scripts/prove_...sh — purpose\n\n"
            "Offending line(s):\n  - " + "\n  - ".join(bad_lines)
        )

    filtered: list[str] = []
    for ln in kept:
        m = BULLET_RE.match(ln)
        if m and m.group(1) == script:
            continue
        filtered.append(ln)

    filtered.append(good)

    uniq: dict[str, str] = {}
    for ln in filtered:
        m = BULLET_RE.match(ln)
        if not m:
            die(f"FAIL: internal error: expected bullet, got: {ln}")
        uniq[m.group(1)] = ln

    keys = sorted(uniq.keys(), key=lambda x: x)
    out = [uniq[k] for k in keys]
    return "\n" + "\n".join(out) + "\n"


def main() -> int:
    args = _get_args()

    if not REG.exists():
        die(f"FAIL: missing {REG}")

    s = REG.read_text(encoding="utf-8")

    pre, surf_mid, post = _split_bounded(s, SURF_BEGIN, SURF_END)
    surf_out = _canon_surface_list(surf_mid, args.script)
    s2 = pre + SURF_BEGIN + surf_out + SURF_END + post

    pre2, run_mid, post2 = _split_bounded(s2, RUN_BEGIN, RUN_END)
    run_out = _canon_ci_proof_runners(run_mid, args.script, args.desc)
    out = pre2 + RUN_BEGIN + run_out + RUN_END + post2

        if out == s:
        print("OK: registry already canonical for requested CI proof runner (no-op).")
        return 0

    REG.write_text(out, encoding="utf-8")
    print("OK: registered CI proof runner into BOTH blocks (canonical, sorted, strict).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
