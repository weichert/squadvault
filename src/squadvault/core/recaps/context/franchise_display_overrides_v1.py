"""franchise_display_overrides_v1 -- Commissioner display override helper.

Provides get_franchise_display_name(), which checks the
franchise_display_overrides table before falling back to
franchise_directory. This is the single choke-point for all
franchise name resolution in display surfaces.

Architecture note: facts are immutable. The override table governs
presentation only -- it never alters canonical_events or memory_events.
An override is itself an append-only record (set_by, set_at, reason).
"""
from __future__ import annotations

from squadvault.core.storage.session import DatabaseSession


def get_franchise_display_name(
    db_path: str,
    league_id: str,
    franchise_id: str,
    season: int,
) -> str:
    """Resolve a franchise_id to its display name for a given season.

    Resolution order:
    1. Check franchise_display_overrides for an active override:
       - Active when league_id matches, franchise_id matches, and
         season_from <= season <= season_to (NULL bounds are open).
       - If suppressed=1 and no display_name_override: return
         "Former Member".
       - If display_name_override is set: return it.
    2. Fall back to franchise_directory for the given season.
    3. Fall back to the raw franchise_id if not found.

    Args:
        db_path: Path to the SQLite database.
        league_id: League identifier (e.g. "70985").
        franchise_id: Franchise slot identifier (e.g. "0010").
        season: The season being displayed.

    Returns:
        Display name string. Never raises.
    """
    with DatabaseSession(db_path) as con:
        # Check for an active override.
        row = con.execute(
            """
            SELECT display_name_override, suppressed, memorial_flag
            FROM franchise_display_overrides
            WHERE league_id = ?
              AND franchise_id = ?
              AND (season_from IS NULL OR season_from <= ?)
              AND (season_to   IS NULL OR season_to   >= ?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (str(league_id), str(franchise_id), int(season), int(season)),
        ).fetchone()

        if row is not None:
            display_name_override, suppressed, _memorial = row
            if display_name_override:
                return str(display_name_override)
            if suppressed:
                return "Former Member"

        # Fall back to franchise_directory for this season.
        fd_row = con.execute(
            """
            SELECT name FROM franchise_directory
            WHERE league_id = ? AND franchise_id = ? AND season = ?
            """,
            (str(league_id), str(franchise_id), int(season)),
        ).fetchone()

    if fd_row and fd_row[0]:
        return str(fd_row[0]).strip()
    return franchise_id


def is_narrative_excluded(
    db_path: str,
    league_id: str,
    franchise_id: str,
    season: int,
) -> bool:
    """Return True if this franchise is excluded from narrative generation.

    A franchise is narrative-excluded when an active override has
    narrative_excluded=1. Suppressed franchises are also narrative-excluded.

    Args:
        db_path: Path to the SQLite database.
        league_id: League identifier.
        franchise_id: Franchise slot identifier.
        season: The season being checked.

    Returns:
        True if the franchise should be skipped in narrative generation.
    """
    with DatabaseSession(db_path) as con:
        row = con.execute(
            """
            SELECT narrative_excluded, suppressed
            FROM franchise_display_overrides
            WHERE league_id = ?
              AND franchise_id = ?
              AND (season_from IS NULL OR season_from <= ?)
              AND (season_to   IS NULL OR season_to   >= ?)
            ORDER BY id DESC
            LIMIT 1
            """,
            (str(league_id), str(franchise_id), int(season), int(season)),
        ).fetchone()
    if row is None:
        return False
    narrative_excluded, suppressed = row
    return bool(narrative_excluded) or bool(suppressed)
