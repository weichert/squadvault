from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from squadvault.config import Config


@dataclass(frozen=True)
class RelationSpec:
    target_database_id: str


@dataclass(frozen=True)
class PropertySpec:
    notion_type: str  # e.g., title, rich_text, number, select, date, url, checkbox, relation
    relation: Optional[RelationSpec] = None


@dataclass(frozen=True)
class DatabaseSpec:
    database_id: str
    title_property: str
    required_properties: Dict[str, PropertySpec]


def build_schema_specs(cfg: Config) -> Dict[str, DatabaseSpec]:
    """
    Authoritative schema expectations for validator.
    Property names must match Notion exactly.
    """
    db = cfg.db

    seasons = DatabaseSpec(
        database_id=db.seasons,
        title_property="Year",
        required_properties={
            "Year": PropertySpec("title"),
        },
    )

    weeks = DatabaseSpec(
        database_id=db.weeks,
        title_property="Key",
        required_properties={
            "Key": PropertySpec("title"),
            "Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.seasons)),
        },
    )

    franchise_season = DatabaseSpec(
        database_id=db.franchise_season,
        title_property="Key",
        required_properties={
            "Key": PropertySpec("title"),
            "Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.seasons)),
            "Franchise ID": PropertySpec("rich_text"),
        },
    )

    weekly_team_results = DatabaseSpec(
        database_id=db.weekly_team_results,
        title_property="Key",
        required_properties={
            "Key": PropertySpec("title"),
            "Week": PropertySpec("relation", relation=RelationSpec(target_database_id=db.weeks)),
            "Franchise Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.franchise_season)),
        },
    )

    matchups = DatabaseSpec(
        database_id=db.matchups,
        title_property="Key",
        required_properties={
            "Key": PropertySpec("title"),
            "Week": PropertySpec("relation", relation=RelationSpec(target_database_id=db.weeks)),
        },
    )

    mfl_api_inventory = DatabaseSpec(
        database_id=db.mfl_api_inventory,
        title_property="Name",
        required_properties={
            "Name": PropertySpec("title"),
        },
    )

    # Ingestion DBs (locked)
    transactions = DatabaseSpec(
        database_id=db.transactions,
        title_property="Key",
        required_properties={
            "Key": PropertySpec("title"),
            "Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.seasons)),
            "Transaction Type": PropertySpec("select"),
            "Transaction Timestamp": PropertySpec("date"),
            "Primary Franchise ID": PropertySpec("rich_text"),
            "Primary Franchise Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.franchise_season)),
            "Players Added IDs": PropertySpec("rich_text"),
            "Players Dropped IDs": PropertySpec("rich_text"),
            "Player IDs Involved": PropertySpec("rich_text"),
            "Bid Amount": PropertySpec("number"),
            "Week": PropertySpec("relation", relation=RelationSpec(target_database_id=db.weeks)),
            "Week Key (Raw)": PropertySpec("rich_text"),
            "Raw MFL JSON": PropertySpec("rich_text"),
            "Raw Source URL": PropertySpec("url"),
        },
    )

    waiver_bids = DatabaseSpec(
        database_id=db.waiver_bids,
        title_property="Key",
        required_properties={
            "Key": PropertySpec("title"),
            "Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.seasons)),
            "Franchise ID (Raw)": PropertySpec("rich_text"),
            "Franchise Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.franchise_season)),
            "Player ID": PropertySpec("rich_text"),
            "Bid Amount": PropertySpec("number"),
            "Winning Bid Amount": PropertySpec("number"),
            "Bid Result": PropertySpec("select"),
            "Won Player?": PropertySpec("checkbox"),
            "Winning Franchise Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.franchise_season)),
            "Processed Timestamp": PropertySpec("date"),
            "Week": PropertySpec("relation", relation=RelationSpec(target_database_id=db.weeks)),
            "Raw MFL JSON": PropertySpec("rich_text"),
            "Raw Source URL": PropertySpec("url"),
        },
    )

    auction_draft_results = DatabaseSpec(
        database_id=db.auction_draft_results,
        title_property="Key",
        required_properties={
            "Key": PropertySpec("title"),
            "Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.seasons)),
            "Franchise Season": PropertySpec("relation", relation=RelationSpec(target_database_id=db.franchise_season)),
            "Franchise ID": PropertySpec("rich_text"),
            "Player ID": PropertySpec("rich_text"),
            "Winning Bid Amount": PropertySpec("number"),
            "Winning Bid Timestamp": PropertySpec("date"),
            "Raw MFL JSON": PropertySpec("rich_text"),
            "Raw Source URL": PropertySpec("url"),
        },
    )

    return {
        "Seasons": seasons,
        "Weeks": weeks,
        "Franchise Season": franchise_season,
        "Weekly Team Results": weekly_team_results,
        "Matchups": matchups,
        "MFL API Inventory": mfl_api_inventory,
        "Transactions": transactions,
        "Waiver Bids": waiver_bids,
        "Auction Draft Results": auction_draft_results,
    }
