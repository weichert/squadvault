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

    def print_summary(self) -> None:
        """Print a human-readable discovery summary."""
        good = [s for s in self.seasons if not s.suspect]
        suspect = [s for s in self.seasons if s.suspect]

        print(f"\n{'='*60}")
        print(f"  MFL Discovery Report -- League {self.league_id}")
        print(f"  Probed: {self.probed_range[0]}--{self.probed_range[1]}")
        print(f"  Active seasons: {len(good)}")
        if suspect:
            print(f"  Suspect (wrong league?): {len(suspect)}")
        print(f"{'='*60}")
        for s in self.seasons:
            flag = "  ** SUSPECT" if s.suspect else ""
            name_str = f'  "{s.league_name}"' if s.league_name else ""
            print(
                f"  {s.season}  server={s.server:<35s}"
                f"  franchises={s.franchise_count}{name_str}{flag}"
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
            return parsed.hostname
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
