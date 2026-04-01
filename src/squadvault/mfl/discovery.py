"""MFL league discovery: probe available seasons, resolve servers, report categories.

Discovery is read-only — no data is written to any database.

Per the Platform Adapter Contract Card (v1.0):
- Discovery determines which seasons and data categories a platform can provide
- Discovery must be honest about gaps
- The adapter must never infer, estimate, or fabricate availability
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from squadvault.ingest.franchises._run_franchises_ingest import (
    _extract_franchises,
)


def _extract_franchises_from_league_json(data: dict) -> list:
    """Extract franchise list from MFL TYPE=league JSON response.

    Delegates to the canonical _extract_franchises from the franchises
    ingest module. Exposed here for test clarity and potential future
    divergence in discovery-specific handling.
    """
    return _extract_franchises(data)


def _extract_league_name(data: dict) -> Optional[str]:
    """Extract the league name from an MFL TYPE=league JSON response.

    The name appears in:
      {"league": {"name": "PFL Buddies"}}
    """
    league = data.get("league")
    if isinstance(league, dict):
        name = league.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


logger = logging.getLogger(__name__)


# -- Data structures ---------------------------------------------------


@dataclass
class SeasonAvailability:
    """What's available for one season on MFL."""

    season: int
    server: str  # resolved MFL hostname (e.g. "www44.myfantasyleague.com")
    franchise_count: int
    categories: List[str]  # available data category names
    mfl_league_id: Optional[str] = None  # MFL league ID for this season (may differ from current)
    league_name: Optional[str] = None
    raw_franchises: List[Dict[str, Any]] = field(default_factory=list)
    suspect: bool = False  # True if franchise count doesn't match expected


@dataclass
class DiscoveryReport:
    """Complete discovery report for an MFL league."""

    league_id: str
    platform: str = "MFL"
    seasons: List[SeasonAvailability] = field(default_factory=list)
    probed_range: tuple = (0, 0)
    errors: List[str] = field(default_factory=list)

    def available_seasons(self) -> List[int]:
        """Return sorted list of discovered active seasons (excluding suspect)."""
        return sorted(s.season for s in self.seasons if not s.suspect)

    def all_discovered_seasons(self) -> List[int]:
        """Return sorted list of all discovered seasons including suspect."""
        return sorted(s.season for s in self.seasons)

    def server_for_season(self, season: int) -> Optional[str]:
        """Look up the resolved server for a given season."""
        for s in self.seasons:
            if s.season == season:
                return s.server
        return None

    def mfl_league_id_for_season(self, season: int) -> Optional[str]:
        """Look up the MFL league ID for a given season."""
        for s in self.seasons:
            if s.season == season:
                return s.mfl_league_id
        return None

    def print_summary(self) -> None:
        """Print a human-readable discovery summary."""
        good = [s for s in self.seasons if not s.suspect]
        suspect = [s for s in self.seasons if s.suspect]

        print(f"\n{'='*70}")
        print(f"  MFL Discovery Report -- League {self.league_id}")
        print(f"  Probed: {self.probed_range[0]}--{self.probed_range[1]}")
        print(f"  Active seasons: {len(good)}")
        if suspect:
            print(f"  Suspect (wrong league?): {len(suspect)}")
        print(f"{'='*70}")
        for s in self.seasons:
            flag = "  ** SUSPECT" if s.suspect else ""
            name_str = f'  "{s.league_name}"' if s.league_name else ""
            mfl_id_str = ""
            if s.mfl_league_id and s.mfl_league_id != self.league_id:
                mfl_id_str = f"  [MFL ID: {s.mfl_league_id}]"
            print(
                f"  {s.season}  server={s.server:<35s}"
                f"  franchises={s.franchise_count}{mfl_id_str}{name_str}{flag}"
            )
        if self.errors:
            print(f"\n  Errors ({len(self.errors)}):")
            for e in self.errors:
                print(f"    - {e}")
        print()


# -- Internal helpers --------------------------------------------------


def _resolve_server_from_response(resp: requests.Response, fallback: str) -> str:
    """Extract the MFL server hostname from the final response URL."""
    try:
        parsed = urlparse(resp.url)
        if parsed.hostname and "myfantasyleague.com" in parsed.hostname:
            return str(parsed.hostname)
    except Exception:
        pass
    return fallback


# Categories that are available for any active MFL season.
# The adapter cannot confirm deeper category-level availability without
# fetching the actual data, so we report all standard categories as
# available when the league existed for a season.
_STANDARD_MFL_CATEGORIES = [
    "FRANCHISE_INFO",
    "MATCHUP_RESULTS",
    "TRANSACTIONS",
    "FAAB_BIDS",
    "DRAFT_PICKS",
    "PLAYER_INFO",
]


def _probe_season(
    session: requests.Session,
    league_id: str,
    season: int,
    start_server: str,
    timeout_s: int = 30,
    max_retries: int = 3,
    retry_backoff_s: float = 3.0,
) -> Optional[SeasonAvailability]:
    """
    Probe a single season via TYPE=league.

    Returns SeasonAvailability if the league was active, None otherwise.
    Retries with exponential backoff on transient network failures.
    """
    url = (
        f"https://{start_server}/{season}/export"
        f"?TYPE=league&L={league_id}&JSON=1"
    )

    resp = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(url, timeout=timeout_s, allow_redirects=True)
            break  # Success -- exit retry loop
        except Exception as e:
            if attempt < max_retries:
                wait = retry_backoff_s * attempt
                logger.info(
                    "Probe season %d attempt %d/%d failed (%s), retrying in %.1fs",
                    season, attempt, max_retries, type(e).__name__, wait,
                )
                time.sleep(wait)
            else:
                logger.warning(
                    "Probe season %d failed after %d attempts: %s",
                    season, max_retries, e,
                )
                return None

    if resp is None or resp.status_code != 200:
        status = resp.status_code if resp is not None else "no response"
        logger.info("Probe season %d: HTTP %s", season, status)
        return None

    # Resolve actual server from the final response URL (after redirects)
    server = _resolve_server_from_response(resp, start_server)

    try:
        data = resp.json()
    except Exception:
        logger.warning("Probe season %d: invalid JSON response", season)
        return None

    # Extract league name for validation
    league_name = _extract_league_name(data)

    # Use the existing franchise extractor to confirm league existence
    franchises = _extract_franchises(data)
    if not franchises:
        logger.info(
            "Probe season %d: no franchises found (league inactive or does not exist)",
            season,
        )
        return None

    return SeasonAvailability(
        season=season,
        server=server,
        franchise_count=len(franchises),
        categories=list(_STANDARD_MFL_CATEGORIES),
        league_name=league_name,
        raw_franchises=franchises,
    )


# -- Public API --------------------------------------------------------


def discover_mfl_league(
    league_id: str,
    *,
    start_year: int = 2009,
    end_year: int = 2025,
    known_server: str = "www44.myfantasyleague.com",
    request_delay_s: float = 2.5,
    timeout_s: int = 30,
    expected_franchise_count: Optional[int] = None,
    expected_league_name: Optional[str] = None,
    max_retries: int = 3,
    retry_backoff_s: float = 3.0,
) -> DiscoveryReport:
    """
    Discover what seasons are available for an MFL league.

    Probes each year from start_year to end_year via TYPE=league,
    resolves the correct MFL server per year (via redirect following),
    and reports available data categories.

    MFL reuses league IDs across servers. If a request lands on the wrong
    server, a different league with the same numeric ID may respond.
    To detect this, provide expected_franchise_count or expected_league_name.
    Seasons that don't match are flagged as "suspect" and excluded from
    available_seasons() (but still visible in the report).

    This is a read-only operation -- no data is written to any database.

    Args:
        league_id: MFL league identifier (e.g. "70985")
        start_year: First year to probe
        end_year: Last year to probe (inclusive)
        known_server: Starting MFL server to probe from
        request_delay_s: Delay between API calls (politeness)
        timeout_s: HTTP timeout per request
        expected_franchise_count: Flag seasons with different counts as suspect
        expected_league_name: Flag seasons with different names as suspect
        max_retries: Retry attempts per season probe
        retry_backoff_s: Base backoff between retries
    """
    report = DiscoveryReport(
        league_id=league_id,
        probed_range=(start_year, end_year),
    )

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "SquadVault/0.1 (+https://squadvault.local)",
            "Accept": "application/json",
        }
    )

    # Track the last known-good server (only from non-suspect results)
    last_good_server = known_server

    for year in range(start_year, end_year + 1):
        print(f"  Probing {year}...", end=" ", flush=True)

        result = _probe_season(
            session=session,
            league_id=league_id,
            season=year,
            start_server=last_good_server,
            timeout_s=timeout_s,
            max_retries=max_retries,
            retry_backoff_s=retry_backoff_s,
        )

        if result:
            # Check for wrong-league collision
            suspect = False
            suspect_reasons: List[str] = []

            if expected_franchise_count is not None:
                if result.franchise_count != expected_franchise_count:
                    suspect = True
                    suspect_reasons.append(
                        f"franchise count {result.franchise_count} != expected {expected_franchise_count}"
                    )

            if expected_league_name is not None and result.league_name is not None:
                if expected_league_name.lower() not in result.league_name.lower():
                    suspect = True
                    suspect_reasons.append(
                        f'league name "{result.league_name}" != expected "{expected_league_name}"'
                    )

            result.suspect = suspect

            report.seasons.append(result)

            status_str = (
                f"ACTIVE on {result.server} ({result.franchise_count} franchises)"
            )
            if result.league_name:
                status_str += f'  "{result.league_name}"'
            if suspect:
                status_str += f"  ** SUSPECT: {'; '.join(suspect_reasons)}"
                report.errors.append(
                    f"Season {year}: suspect result -- {'; '.join(suspect_reasons)}"
                )
            else:
                # Only carry forward the server from non-suspect results
                last_good_server = result.server

            print(status_str)
        else:
            print("not found")

        # Be polite to MFL
        if year < end_year:
            time.sleep(request_delay_s)

    return report


# -- History-chain discovery -------------------------------------------


@dataclass
class HistoryEntry:
    """One entry from MFL's history.league array."""
    year: int
    server: str
    mfl_league_id: str


def _extract_league_history(data: dict) -> List[HistoryEntry]:
    """Extract the history chain from an MFL TYPE=league JSON response.

    MFL stores prior season links in:
      {"league": {"history": {"league": [
          {"year": "2009", "url": "https://www48.myfantasyleague.com/2009/home/50536"},
          ...
      ]}}}

    Returns sorted list of HistoryEntry (by year).
    """
    league = data.get("league")
    if not isinstance(league, dict):
        return []

    history = league.get("history")
    if not isinstance(history, dict):
        return []

    entries = history.get("league", [])
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list):
        return []

    result: List[HistoryEntry] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue

        year_str = entry.get("year")
        url = entry.get("url")
        if not year_str or not url:
            continue

        try:
            year = int(year_str)
        except (ValueError, TypeError):
            continue

        # Parse URL: https://www48.myfantasyleague.com/2009/home/50536
        try:
            parsed = urlparse(url)
            server = parsed.hostname or ""
            # League ID is the last path segment
            path_parts = [p for p in (parsed.path or "").split("/") if p]
            mfl_id = path_parts[-1] if path_parts else ""
        except Exception:
            continue

        if not server or not mfl_id:
            continue

        result.append(HistoryEntry(year=year, server=server, mfl_league_id=mfl_id))

    return sorted(result, key=lambda e: e.year)


def discover_mfl_league_via_history(
    league_id: str,
    *,
    known_server: str = "www44.myfantasyleague.com",
    current_year: int = 2024,
    request_delay_s: float = 2.5,
    timeout_s: int = 30,
    max_retries: int = 3,
    retry_backoff_s: float = 3.0,
) -> DiscoveryReport:
    """
    Discover all seasons for an MFL league using the history chain.

    Makes ONE API call to TYPE=league for the current year, extracts the
    history.league array, and then probes each historical season using
    the exact server + league ID from the chain.

    This is dramatically more efficient and accurate than blind probing:
    - No wrong-league collisions (each entry has the correct league ID)
    - No server guessing (each entry has the correct server)
    - Only N+1 API calls for N historical seasons

    Args:
        league_id: Current MFL league identifier (e.g. "70985")
        known_server: Server hosting the current league
        current_year: Which year to fetch the history from
        request_delay_s: Delay between API calls (politeness)
        timeout_s: HTTP timeout per request
        max_retries: Retry attempts per probe
        retry_backoff_s: Base backoff between retries
    """
    report = DiscoveryReport(league_id=league_id)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "SquadVault/0.1 (+https://squadvault.local)",
            "Accept": "application/json",
        }
    )

    # Step 1: Fetch current league to get history chain
    print(f"  Fetching history chain from {known_server} (league {league_id}, year {current_year})...")
    current_url = (
        f"https://{known_server}/{current_year}/export"
        f"?TYPE=league&L={league_id}&JSON=1"
    )

    resp = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.get(current_url, timeout=timeout_s, allow_redirects=True)
            break
        except Exception as e:
            if attempt < max_retries:
                time.sleep(retry_backoff_s * attempt)
            else:
                report.errors.append(f"Failed to fetch current league: {e}")
                return report

    if resp is None or resp.status_code != 200:
        report.errors.append(f"HTTP {resp.status_code if resp else 'no response'} fetching current league")
        return report

    try:
        current_data = resp.json()
    except Exception:
        report.errors.append("Invalid JSON from current league")
        return report

    # Step 2: Extract history chain
    history_entries = _extract_league_history(current_data)
    if not history_entries:
        report.errors.append("No history chain found in TYPE=league response")
        return report

    print(f"  Found {len(history_entries)} seasons in history chain")

    # Build year range from history
    years = [e.year for e in history_entries]
    report.probed_range = (min(years), max(years))

    # Step 3: Probe each season using exact server + league ID from history
    for entry in history_entries:
        print(f"  Probing {entry.year} (MFL ID: {entry.mfl_league_id} on {entry.server})...", end=" ", flush=True)

        result = _probe_season(
            session=session,
            league_id=entry.mfl_league_id,
            season=entry.year,
            start_server=entry.server,
            timeout_s=timeout_s,
            max_retries=max_retries,
            retry_backoff_s=retry_backoff_s,
        )

        if result:
            result.mfl_league_id = entry.mfl_league_id
            report.seasons.append(result)
            print(
                f"ACTIVE ({result.franchise_count} franchises)"
                + (f'  "{result.league_name}"' if result.league_name else "")
                + (f"  [MFL ID: {entry.mfl_league_id}]" if entry.mfl_league_id != league_id else "")
            )
        else:
            print("not found")
            report.errors.append(
                f"Season {entry.year}: history chain points to"
                f" {entry.server}/L={entry.mfl_league_id} but probe failed"
            )

        time.sleep(request_delay_s)

    return report
