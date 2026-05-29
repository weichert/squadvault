#!/usr/bin/env python3
"""sync_archive_to_supabase.py — Filesystem-source archive sync to Supabase.

Reads the three Permanent Records archive surfaces from the engine repo
filesystem and syncs them to Supabase staging as SEASON_RETROSPECTIVE
artifacts. Sibling to scripts/sync_to_supabase.py, which handles DB-state
artifacts (E1, F1).

SCOPE (Milestone 4, Phase 11):
  Surface                          Class  Filesystem path
  ──────────────────────────────── ────── ────────────────────────────────
  Hall of Fame & Shame             A1     archive/hall_of_fame_and_shame/
  Draft History Vault              A2     archive/draft_history_vault/
  Championship Timeline            A3     archive/championship_timeline/

  E1 (WEEKLY_RECAP) and F1 (RIVALRY_CHRONICLE) — NOT in scope; use
  sync_to_supabase.py for those (DB-state lifecycle).

GOVERNANCE MODEL:
  Filesystem artifacts have a different lifecycle than DB-state ones:
  the git commit that lands a regeneration IS the commissioner's
  approval event. This script therefore:
    - Reads the engine repo's working tree (not a database table)
    - Refuses to sync a surface with uncommitted changes (governance
      requires the commit to have landed)
    - Derives approved_at / approved_by from `git log` of the surface
      directory
    - Encodes the regeneration event in the synthetic engine_artifact_id
      and the docket: archive:<surface>:<short-sha> and
      SV-{CLASS}-{YEAR}-{SHORTSHA} respectively

IDEMPOTENCY:
  Unlike sync_to_supabase.py (which keys on engine_artifact_id from a
  stable integer row id), filesystem sources have a synthetic id that
  changes whenever the regen commit changes. Dedupe is therefore by
  content hash:
    (league_id, artifact_class, engine_source_hash, is_demo=false)
  If a row with that triple already exists, the current run is a no-op
  for that surface (SKIP). Otherwise a brand-new artifacts row is
  INSERTed with a fresh synthetic id and a fresh sha-bearing docket.
  Old regenerations remain queryable by direct URL; the records page
  surfaces newest-per-class via ORDER BY approved_at DESC.

CONCATENATION:
  Each surface has an index.md + three sub-pages. This script:
    1. Reads index.md to determine sub-page ordering (link order)
    2. Reads each sub-page to extract its H1 heading
    3. Rewrites `./<sub>.md` links in the index to in-page `#slug`
       anchors derived from each sub-page's H1
    4. Concatenates index + sub-pages in link order, separated by `---`
  The lead paragraph repetition that appears across files (a generator
  convention) is preserved as-is — the sync layer does not rewrite
  narrative content. If the repetition becomes a UX concern, address
  it upstream in the generator scripts.

USAGE:
  ./scripts/py scripts/sync_archive_to_supabase.py --dry-run
  ./scripts/py scripts/sync_archive_to_supabase.py --surface championship_timeline
  ./scripts/py scripts/sync_archive_to_supabase.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# Third-party (already in engine repo requirements per M3)
from supabase import Client, create_client

# ─── Constants ───────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = REPO_ROOT / "archive"

DEFAULT_LEAGUE_CANONICAL_ID = "70985"

# CERTIFIED trust bar (middle dot, not pipe — Design Brief §8).
# Note: the artifacts.trust_bar_text column default in Supabase staging
# uses a pipe; we override it on every INSERT. Filed as a follow-up DB
# migration outside M4 scope.
TRUST_BAR_CERTIFIED = (
    "Entered into the Record \u00b7 Source Facts Verified \u00b7 SquadVault"
)

# Surface name -> (artifact_class, frontend_title)
# Class assignments match weichert/squadvault-frontend records bindings
# (archive/page.tsx, archive/records/page.tsx,
#  archive/records/[artifactId]/page.tsx, all at frontend HEAD 3466a65).
SURFACE_MAPPING: dict[str, tuple[str, str]] = {
    "hall_of_fame_and_shame": ("A1", "Hall of Fame & Shame"),
    "draft_history_vault":    ("A2", "Draft History Vault"),
    "championship_timeline":  ("A3", "Championship Timeline"),
}

# Most-recent-covered season. Surfaces aggregate league history through
# this season; bump in one place when a new season's data lands.
DEFAULT_THROUGH_SEASON = 2025

SUPABASE_ARTIFACT_TYPE = "SEASON_RETROSPECTIVE"
SECTION_SEPARATOR = "\n\n---\n\n"

# ─── Logging ─────────────────────────────────────────────────────────────────

log = logging.getLogger("sync_archive_to_supabase")


def _configure_logging(verbose: bool, log_file: Path | None) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s %(levelname)-7s %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=level, format=fmt, handlers=handlers, force=True)


# ─── Filesystem read model ───────────────────────────────────────────────────

INDEX_LINK_RE = re.compile(r"\[([^\]]+)\]\(\./([A-Za-z0-9_\-]+\.md)\)")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ArchiveArtifact:
    """A single surface bundle — concatenated content + provenance."""

    surface: str
    artifact_class: str       # A1 / A2 / A3
    frontend_title: str
    season: int               # most-recent-covered season
    content_markdown: str     # concatenated, link-rewritten
    source_hash: str          # sha256 of content_markdown
    short_sha: str            # 7-char git sha of last commit touching surface
    approved_at: str          # ISO timestamp of that commit
    approved_by: str          # git author name of that commit
    source_files: tuple[str, ...]   # filenames included, in order

    @property
    def engine_artifact_id(self) -> str:
        """Synthetic id keyed on regen-event sha (not content sha).

        Two rows can share this id only if the same commit was re-synced
        after a hand-edit broke the commit→content correspondence; the
        --check-clean preflight refuses to sync that state.
        """
        return f"archive:{self.surface}:{self.short_sha}"

    @property
    def docket_id(self) -> str:
        """SV-{CLASS}-{YEAR}-{SHORTSHA} — sha-bearing, collision-free."""
        return f"SV-{self.artifact_class}-{self.season}-{self.short_sha}"


def _slugify(heading: str) -> str:
    """GitHub-style anchor slug from a markdown heading text.

    Lowercase, hyphenate whitespace, strip punctuation except hyphens.
    """
    s = heading.strip().lower()
    s = re.sub(r"[^\w\s\-]", "", s)        # drop punctuation (keep \w, \s, -)
    s = re.sub(r"[\s_]+", "-", s)          # whitespace/underscores -> hyphen
    s = re.sub(r"-+", "-", s).strip("-")   # collapse, trim
    return s


def _parse_index_link_order(index_md: str) -> list[str]:
    """Return sub-page filenames in the order they appear linked in index.md.

    Only `./<name>.md` style links are considered; absolute URLs and
    other link forms are ignored.
    """
    seen: list[str] = []
    for _label, filename in INDEX_LINK_RE.findall(index_md):
        if filename not in seen:
            seen.append(filename)
    return seen


def _extract_h1(content: str, fallback: str) -> str:
    """Return the first H1 heading text from `content`, or `fallback`."""
    m = H1_RE.search(content)
    return m.group(1).strip() if m else fallback


def _rewrite_index_links(
    index_md: str, sub_anchors: dict[str, str]
) -> str:
    """Rewrite `[Label](./file.md)` -> `[Label](#anchor)` in the index body.

    Files without a corresponding anchor (shouldn't happen for our
    surfaces) are left untouched so the failure is visible at review.
    """

    def _repl(match: re.Match[str]) -> str:
        label, filename = match.group(1), match.group(2)
        anchor = sub_anchors.get(filename)
        if anchor is None:
            log.warning(
                "Link target %r in index has no matching sub-page H1; "
                "leaving link unrewritten.", filename,
            )
            return match.group(0)
        return f"[{label}](#{anchor})"

    return INDEX_LINK_RE.sub(_repl, index_md)


def _surface_is_clean(surface_dir: Path) -> tuple[bool, str]:
    """Return (clean, details). Clean = no uncommitted changes in surface."""
    rel = surface_dir.relative_to(REPO_ROOT)
    # --untracked-files=no: ignore unstaged new files outside the working tree
    # We want: any tracked file that differs from HEAD blocks sync.
    porcelain = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no", "--", str(rel)],
        cwd=REPO_ROOT,
    ).decode().strip()
    if porcelain:
        return False, porcelain
    return True, ""


def _surface_git_provenance(surface_dir: Path) -> tuple[str, str, str]:
    """Return (short_sha, iso_timestamp, author_name) for the most recent
    commit touching this surface directory.
    """
    rel = str(surface_dir.relative_to(REPO_ROOT))
    raw = subprocess.check_output(
        ["git", "log", "-1", "--format=%h%x1f%aI%x1f%an", "--abbrev=7", "--", rel],
        cwd=REPO_ROOT,
    ).decode().strip()
    if not raw:
        raise RuntimeError(
            f"No git history for surface dir {rel!r}. Has it been committed?"
        )
    short_sha, iso_ts, author = raw.split("\x1f", 2)
    return short_sha, iso_ts, author


def _build_archive_artifact(surface: str, *, through_season: int) -> ArchiveArtifact:
    """Read disk, build the concatenated artifact bundle for one surface."""
    surface_dir = ARCHIVE_ROOT / surface
    if not surface_dir.is_dir():
        raise FileNotFoundError(f"Surface directory missing: {surface_dir}")

    artifact_class, frontend_title = SURFACE_MAPPING[surface]

    # Clean-tree preflight (governance: commit IS the approval event).
    clean, details = _surface_is_clean(surface_dir)
    if not clean:
        raise RuntimeError(
            f"Surface {surface!r} has uncommitted changes; cannot sync. "
            f"Commit the regeneration first.\n{details}"
        )

    index_path = surface_dir / "index.md"
    if not index_path.is_file():
        raise FileNotFoundError(f"Missing index.md in {surface_dir}")

    index_md = index_path.read_text(encoding="utf-8")
    ordered_subpages = _parse_index_link_order(index_md)

    # Read all sub-pages, build anchor map (filename -> slug).
    sub_anchors: dict[str, str] = {}
    sub_contents: dict[str, str] = {}
    for filename in ordered_subpages:
        path = surface_dir / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"Sub-page {filename!r} linked from index.md missing in {surface_dir}"
            )
        body = path.read_text(encoding="utf-8")
        sub_contents[filename] = body
        h1 = _extract_h1(body, fallback=filename.rsplit(".", 1)[0])
        sub_anchors[filename] = _slugify(h1)

    # Rewrite index links to in-page anchors.
    rewritten_index = _rewrite_index_links(index_md, sub_anchors)

    # Concatenate: index first, then sub-pages in link order.
    parts: list[str] = [rewritten_index.rstrip()]
    for filename in ordered_subpages:
        parts.append(sub_contents[filename].rstrip())
    content = SECTION_SEPARATOR.join(parts) + "\n"

    short_sha, iso_ts, author = _surface_git_provenance(surface_dir)
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    source_files = ("index.md", *ordered_subpages)

    return ArchiveArtifact(
        surface=surface,
        artifact_class=artifact_class,
        frontend_title=frontend_title,
        season=through_season,
        content_markdown=content,
        source_hash=content_hash,
        short_sha=short_sha,
        approved_at=iso_ts,
        approved_by=author,
        source_files=source_files,
    )


def _load_archive_artifacts(
    *, surfaces: tuple[str, ...], through_season: int,
) -> Iterator[ArchiveArtifact]:
    for surface in surfaces:
        if surface not in SURFACE_MAPPING:
            raise ValueError(
                f"Unknown surface {surface!r}; valid: {sorted(SURFACE_MAPPING)}"
            )
        yield _build_archive_artifact(surface, through_season=through_season)


# ─── Supabase write model ────────────────────────────────────────────────────

def _resolve_league_uuid(client: Client, canonical_id: str) -> str:
    resp = (
        client.table("leagues")
        .select("id")
        .eq("canonical_id", canonical_id)
        .single()
        .execute()
    )
    if not resp.data or "id" not in resp.data:
        raise RuntimeError(
            f"League with canonical_id={canonical_id!r} not found in Supabase. "
            f"Seed it before running sync.",
        )
    return str(resp.data["id"])


def _find_existing_artifact_by_content(
    client: Client,
    *,
    league_uuid: str,
    artifact_class: str,
    source_hash: str,
) -> dict | None:
    """Filesystem-source idempotency: dedupe by (league, class, content-hash).

    Unlike sync_to_supabase.py which keys on engine_artifact_id (a stable
    integer row id), the filesystem synthetic id changes with the git sha
    and is therefore unreliable for dedupe.
    """
    resp = (
        client.table("artifacts")
        .select("id, current_version, engine_source_hash, docket_id, approved_at")
        .eq("league_id", league_uuid)
        .eq("artifact_class", artifact_class)
        .eq("engine_source_hash", source_hash)
        .eq("is_demo", False)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def _insert_new_artifact(
    client: Client,
    *,
    league_uuid: str,
    artifact: ArchiveArtifact,
) -> str:
    """Insert artifacts row + artifact_versions v1 + docket_ids row.

    Returns the new artifacts row uuid.
    """
    artifact_resp = (
        client.table("artifacts")
        .insert(
            {
                "league_id":          league_uuid,
                "artifact_type":      SUPABASE_ARTIFACT_TYPE,
                "artifact_class":     artifact.artifact_class,
                "season":             artifact.season,
                "week_index":         None,   # nullable; no week for A1/A2/A3
                "engine_artifact_id": artifact.engine_artifact_id,
                "engine_source_hash": artifact.source_hash,
                "approval_state":     "APPROVED",
                "current_version":    1,
                "is_demo":            False,
                "docket_id":          artifact.docket_id,
                "trust_bar_text":     TRUST_BAR_CERTIFIED,
                "approved_at":        artifact.approved_at,
            }
        )
        .execute()
    )
    if not artifact_resp.data:
        raise RuntimeError(
            f"Insert artifacts returned no row for surface={artifact.surface!r}"
        )
    artifact_uuid = str(artifact_resp.data[0]["id"])

    client.table("artifact_versions").insert(
        {
            "artifact_id":      artifact_uuid,
            "version":          1,
            "content_markdown": artifact.content_markdown,
            "generated_by":     "engine",
        }
    ).execute()

    client.table("docket_ids").insert(
        {
            "artifact_id":     artifact_uuid,
            "docket_value":    artifact.docket_id,
            "year":            artifact.season,
            "sequence_number": 1,   # filesystem artifacts have no version counter
            "is_demo":         False,
        }
    ).execute()

    return artifact_uuid


# ─── Sync orchestration ──────────────────────────────────────────────────────

@dataclass
class RunCounts:
    inserted: int = 0
    skipped: int = 0
    failed: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "inserted": self.inserted,
            "skipped":  self.skipped,
            "failed":   self.failed,
        }


def _sync_one(
    client: Client | None,
    league_uuid: str,
    artifact: ArchiveArtifact,
    *,
    dry_run: bool,
    counts: RunCounts,
) -> None:
    tag = (
        f"surface={artifact.surface} class={artifact.artifact_class} "
        f"sha={artifact.short_sha}"
    )

    try:
        if dry_run:
            log.info(
                "[DRY] WOULD-INSERT %s  docket=%s engine_id=%s hash=%s",
                tag, artifact.docket_id, artifact.engine_artifact_id,
                artifact.source_hash[:12],
            )
            counts.inserted += 1
            return

        assert client is not None
        existing = _find_existing_artifact_by_content(
            client,
            league_uuid=league_uuid,
            artifact_class=artifact.artifact_class,
            source_hash=artifact.source_hash,
        )

        if existing is not None:
            log.info(
                "SKIP   %s  (content unchanged; matches existing artifact=%s docket=%s)",
                tag, existing["id"], existing["docket_id"],
            )
            counts.skipped += 1
            return

        uuid = _insert_new_artifact(
            client,
            league_uuid=league_uuid,
            artifact=artifact,
        )
        log.info(
            "INSERT %s  -> artifact=%s docket=%s approved_at=%s by=%s",
            tag, uuid, artifact.docket_id, artifact.approved_at,
            artifact.approved_by,
        )
        counts.inserted += 1

    except Exception as exc:   # per-artifact roll back, batch continues
        counts.failed += 1
        log.error("FAILED %s — %s: %s", tag, type(exc).__name__, exc)


def _engine_git_hash() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _write_sync_log(
    client: Client,
    *,
    status: str,
    counts: RunCounts,
    surfaces_synced: tuple[str, ...],
    git_hash: str | None,
    error: str | None,
) -> None:
    client.table("sync_log").insert(
        {
            "engine_git_hash": git_hash,
            "tables_synced":   {
                "engine_types": [SUPABASE_ARTIFACT_TYPE],
                "surfaces":     list(surfaces_synced),
                "source_model": "filesystem",
            },
            "row_counts":      counts.as_dict(),
            "status":          status,
            "error_message":   error,
        }
    ).execute()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Sync filesystem-source archive surfaces (A1/A2/A3) to "
            "Supabase staging as SEASON_RETROSPECTIVE artifacts."
        ),
    )
    p.add_argument("--dry-run", action="store_true",
                   help="Read and plan; do not write to Supabase.")
    p.add_argument("--surface", choices=sorted(SURFACE_MAPPING), default=None,
                   help="Restrict to a single surface. Default: all three.")
    p.add_argument("--league-canonical-id", default=DEFAULT_LEAGUE_CANONICAL_ID,
                   help="MFL canonical league id (default: PFL Buddies / 70985).")
    p.add_argument("--through-season", type=int, default=DEFAULT_THROUGH_SEASON,
                   help=(f"Most-recent-covered season for docket/year "
                         f"(default: {DEFAULT_THROUGH_SEASON})."))
    p.add_argument("--verbose", "-v", action="store_true",
                   help="DEBUG-level logging.")
    return p.parse_args(argv)


def _build_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in env "
            "(propagate .env.local with `set -a; source .env.local; set +a`).",
        )
    return create_client(url, key)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    log_file = Path("logs") / f"sync_archive_to_supabase_{today}.log"
    _configure_logging(args.verbose, log_file=None if args.dry_run else log_file)

    surfaces = (
        (args.surface,) if args.surface else tuple(SURFACE_MAPPING.keys())
    )
    git_hash = _engine_git_hash()

    log.info("─" * 60)
    log.info(
        "sync_archive_to_supabase  dry_run=%s  surfaces=%s  through_season=%s",
        args.dry_run, surfaces, args.through_season,
    )
    log.info("engine git HEAD: %s", git_hash or "(unknown)")

    client: Client | None = None
    league_uuid = "<dry-run>"
    if not args.dry_run:
        client = _build_client()
        league_uuid = _resolve_league_uuid(client, args.league_canonical_id)
        log.info(
            "Supabase league_id resolved: %s -> %s",
            args.league_canonical_id, league_uuid,
        )

    counts = RunCounts()
    run_status = "success"
    run_error: str | None = None

    try:
        for artifact in _load_archive_artifacts(
            surfaces=surfaces, through_season=args.through_season,
        ):
            _sync_one(client, league_uuid, artifact, dry_run=args.dry_run, counts=counts)
    except Exception as exc:   # batch-level failure (e.g. dirty surface)
        run_status = "error"
        run_error = f"{type(exc).__name__}: {exc}"
        log.exception("Batch aborted: %s", run_error)

    log.info("Counts: %s", json.dumps(counts.as_dict()))

    if not args.dry_run and client is not None:
        try:
            _write_sync_log(
                client,
                status=run_status if counts.failed == 0 else "partial",
                counts=counts,
                surfaces_synced=surfaces,
                git_hash=git_hash,
                error=run_error,
            )
        except Exception as exc:
            log.error("Failed to write sync_log row: %s: %s", type(exc).__name__, exc)

    return 0 if (run_status == "success" and counts.failed == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
