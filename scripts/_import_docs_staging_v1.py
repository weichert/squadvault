#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ManifestRow:
    source: Path
    dest_rel: Path
    label: str | None = None


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def parse_manifest(manifest_path: Path) -> list[ManifestRow]:
    if not manifest_path.exists():
        die(f"manifest not found: {manifest_path}")

    rows: list[ManifestRow] = []
    with manifest_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"source_path", "dest_rel_path"}
        if reader.fieldnames is None:
            die("manifest has no header row")
        missing = required - set(reader.fieldnames)
        if missing:
            die(f"manifest missing required columns: {sorted(missing)}")

        for i, r in enumerate(reader, start=2):
            src_raw = (r.get("source_path") or "").strip()
            dst_raw = (r.get("dest_rel_path") or "").strip()
            label = (r.get("label") or "").strip() or None

            if not src_raw or not dst_raw:
                die(f"manifest row {i}: source_path and dest_rel_path must be non-empty")

            src = Path(src_raw)
            dst = Path(dst_raw)

            if src.is_absolute():
                die(f"manifest row {i}: source_path must be repo-relative (got absolute): {src}")

            if dst.is_absolute():
                die(f"manifest row {i}: dest_rel_path must be relative (got absolute): {dst}")

            if not str(dst).replace("\\", "/").startswith("docs/"):
                die(f"manifest row {i}: dest_rel_path must start with 'docs/': {dst}")

            if ".." in dst.parts:
                die(f"manifest row {i}: dest_rel_path must not contain '..': {dst}")

            rows.append(ManifestRow(source=src, dest_rel=dst, label=label))

    # Duplicate destination detection (ambiguity)
    seen: dict[Path, list[ManifestRow]] = {}
    for row in rows:
        seen.setdefault(row.dest_rel, []).append(row)
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    if dups:
        msg = "manifest has duplicate dest_rel_path entries:\n"
        for dst, rr in sorted(dups.items(), key=lambda x: str(x[0])):
            msg += f"  - {dst} <= {', '.join(str(r.source) for r in rr)}\n"
        die(msg.rstrip())

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic docs import: docs/_import/manifest.tsv → canonical docs/ tree"
    )
    ap.add_argument(
        "--manifest",
        default="docs/_import/manifest.tsv",
        help="TSV with columns: source_path, dest_rel_path, optional label",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions only; do not copy",
    )
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    manifest_path = (repo_root / args.manifest).resolve()
    rows = parse_manifest(manifest_path)

    print(f"repo_root: {repo_root}")
    print(f"manifest:  {manifest_path}")
    print(f"rows:      {len(rows)}")
    print()

    plan: list[tuple[ManifestRow, Path, str]] = []
    for row in rows:
        src_abs = (repo_root / row.source).resolve()
        if not src_abs.exists():
            die(f"missing source file: {row.source} (abs: {src_abs})")
        if not src_abs.is_file():
            die(f"source is not a file: {row.source} (abs: {src_abs})")

        dest_abs = (repo_root / row.dest_rel).resolve()

        # Guard: dest must remain under repo_root/docs after resolution
        if repo_root not in dest_abs.parents:
            die(f"dest resolves outside repo_root (path traversal?): {row.dest_rel} -> {dest_abs}")
        docs_root = (repo_root / "docs").resolve()
        if docs_root not in dest_abs.parents:
            die(f"dest must be under docs/: {dest_abs}")

        src_hash = sha256_file(src_abs)
        plan.append((row, dest_abs, src_hash))

    # Print plan deterministically
    for row, dest_abs, src_hash in plan:
        lbl = f" [{row.label}]" if row.label else ""
        print(f"-{lbl} {row.source}")
        print(f"    -> {row.dest_rel}")
        print(f"    sha256={src_hash}")
    print()

    changed = 0
    for row, dest_abs, src_hash in plan:
        src_abs = (repo_root / row.source).resolve()
        dest_abs.parent.mkdir(parents=True, exist_ok=True)

        if dest_abs.exists():
            if not dest_abs.is_file():
                die(f"destination exists but is not a file: {dest_abs}")

            dst_hash = sha256_file(dest_abs)
            if dst_hash == src_hash:
                print(f"OK (idempotent): {row.dest_rel}")
                continue

            die(
                "refusing to overwrite non-identical destination:\n"
                f"  dest: {row.dest_rel}\n"
                f"  dest_sha256: {dst_hash}\n"
                f"  src:  {row.source}\n"
                f"  src_sha256:  {src_hash}\n"
                "Resolve by changing dest_rel_path (archive), or delete/move the existing file explicitly."
            )

        if args.dry_run:
            print(f"DRY-RUN: copy {row.source} -> {row.dest_rel}")
        else:
            shutil.copy2(src_abs, dest_abs)
            print(f"COPIED: {row.dest_rel}")
            changed += 1

    print()
    if args.dry_run:
        print("DONE (dry-run).")
    else:
        print(f"DONE. files_copied={changed}, total_rows={len(plan)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
