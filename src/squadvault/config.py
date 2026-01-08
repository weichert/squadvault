from __future__ import annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import os


@dataclass(frozen=True)
class NotionDBIds:
    seasons: str
    weeks: str
    franchise_season: str
    weekly_team_results: str
    matchups: str
    mfl_api_inventory: str
    auction_draft_results: str
    waiver_bids: str
    transactions: str


@dataclass(frozen=True)
class Config:
    notion_api_key: str
    notion_version: str

    mfl_league_id: str
    mfl_server: str
    mfl_username: str | None
    mfl_password: str | None

    db: NotionDBIds

    log_level: str
    raw_json_truncate_chars: int


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if val is None or not val.strip():
        raise RuntimeError(f"Missing required env var: {name}")
    return val.strip()


def load_config() -> Config:
    load_dotenv()

    notion_api_key = _require_env("NOTION_API_KEY")
    notion_version = os.getenv("NOTION_VERSION", "2022-06-28").strip()

    mfl_league_id = _require_env("MFL_LEAGUE_ID")
    mfl_server = os.getenv("MFL_SERVER", "44").strip()
    mfl_username = os.getenv("MFL_USERNAME")
    mfl_password = os.getenv("MFL_PASSWORD")

    db = NotionDBIds(
        seasons=_require_env("NOTION_DB_SEASONS"),
        weeks=_require_env("NOTION_DB_WEEKS"),
        franchise_season=_require_env("NOTION_DB_FRANCHISE_SEASON"),
        weekly_team_results=_require_env("NOTION_DB_WEEKLY_TEAM_RESULTS"),
        matchups=_require_env("NOTION_DB_MATCHUPS"),
        mfl_api_inventory=_require_env("NOTION_DB_MFL_API_INVENTORY"),
        auction_draft_results=_require_env("NOTION_DB_AUCTION_DRAFT_RESULTS"),
        waiver_bids=_require_env("NOTION_DB_WAIVER_BIDS"),
        transactions=_require_env("NOTION_DB_TRANSACTIONS"),
    )

    log_level = os.getenv("LOG_LEVEL", "INFO").strip()
    raw_json_truncate_chars = int(os.getenv("RAW_JSON_TRUNCATE_CHARS", "1900").strip())

    return Config(
        notion_api_key=notion_api_key,
        notion_version=notion_version,
        mfl_league_id=mfl_league_id,
        mfl_server=mfl_server,
        mfl_username=mfl_username.strip() if mfl_username and mfl_username.strip() else None,
        mfl_password=mfl_password.strip() if mfl_password and mfl_password.strip() else None,
        db=db,
        log_level=log_level,
        raw_json_truncate_chars=raw_json_truncate_chars,
    )
