from __future__ import annotations

from pathlib import Path

INDEX = Path("docs/80_indices/ops/CI_Guardrails_Index_v1.0.md")

TO_DELETE = [
    Path("scripts/prove_local_clean_then_ci_v1.sh"),
    Path("scripts/_patch_add_prove_local_clean_then_ci_v1.py"),
    Path("scripts/patch_add_prove_local_clean_then_ci_v1.sh"),
    Path("scripts/prove_local_clean_then_ci_v2.sh"),
    Path("scripts/_patch_add_prove_local_clean_then_ci_v2.py"),
    Path("scripts/patch_add_prove_local_clean_then_ci_v2.sh"),
]

# Defensive fingerprints (fail-closed): we only delete if these markers are present.
EXPECTED_MARKERS = {
    Path("scripts/prove_local_clean_then_ci_v1.sh"): "local scratch cleanup + CI prove helper (v1)",
    Path("scripts/_patch_add_prove_local_clean_then_ci_v1.py"): 'TARGET = Path("scripts/prove_local_clean_then_ci_v1.sh")',
    Path("scripts/patch_add_prove_local_clean_then_ci_v1.sh"): "add prove_local_clean_then_ci_v1 helper (v1)",
    Path("scripts/prove_local_clean_then_ci_v2.sh"): "local scratch cleanup + CI prove helper (v2)",
    Path("scripts/_patch_add_prove_local_clean_then_ci_v2.py"): 'TARGET = Path("scripts/prove_local_clean_then_ci_v2.sh")',
    Path("scripts/patch_add_prove_local_clean_then_ci_v2.sh"): "add prove_local_clean_then_ci_v2 helper (v2)",
}


def _die(msg: str) -> None:
    raise SystemExit(f"ERROR: {msg}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_expected_contents(path: Path) -> None:
    if not path.exists():
        return
    marker = EXPECTED_MARKERS.get(path)
    if not marker:
        _die(f"internal: missing expected marker for {path}")
    txt = _read(path)
    if marker not in txt:
        _die(f"refusing to delete {path}: expected marker not found (file changed unexpectedly)")


def _delete_file(path: Path) -> None:
    if path.exists():
        path.unlink()


def _patch_index() -> None:
    if not INDEX.exists():
        return

    txt = _read(INDEX)

    # remove any v1/v2 references; keep v3
    lines = txt.splitlines(True)
    out: list[str] = []
    for ln in lines:
        if "prove_local_clean_then_ci_v1.sh" in ln:
            continue
        if "prove_local_clean_then_ci_v2.sh" in ln:
            continue
        out.append(ln)

    new_txt = "".join(out)
    if new_txt != txt:
        INDEX.write_text(new_txt, encoding="utf-8")


def main() -> None:
    # Safety: verify the files we intend to delete still look like the expected v1/v2 artifacts.
    for p in TO_DELETE:
        _assert_expected_contents(p)

    _patch_index()

    for p in TO_DELETE:
        _delete_file(p)

    print("OK: retired prove_local_clean_then_ci v1/v2 (deleted scripts + removed index references where applicable)")


if __name__ == "__main__":
    main()
