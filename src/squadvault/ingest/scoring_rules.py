"""Ingest league scoring rules from MFL rules endpoint.

Parses the MFL TYPE=rules API response and stores the raw JSON plus
extracted key scoring parameters in the league_scoring_rules metadata
table. One API call per season.

This is league configuration data, not activity. It does not create
canonical events — it creates reference metadata used by Dimension 11
(Scoring Rules Context) detector.

MFL response shape (abbreviated):
  {"rules": {"positionRules": [{"positions": "QB|...", "rule": [
    {"event": {"$t": "#P"}, "points": {"$t": "*6"}}, ...
  ]}]}}

Key MFL scoring event codes:
  #P = passing TD, PY = passing yards, IN = interception
  #R = rushing TD, RY = rushing yards
  #C = receiving TD, CY = receiving yards, CC = reception (catch)
  FG = field goal, PA = points allowed (defense)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from squadvault.core.storage.session import DatabaseSession

logger = logging.getLogger(__name__)


# Standard fantasy scoring benchmarks for comparison
STANDARD_SCORING = {
    "passing_td_pts": 4.0,
    "passing_yd_pts": 0.04,  # 25 yards per point
    "rushing_td_pts": 6.0,
    "rushing_yd_pts": 0.1,   # 10 yards per point
    "receiving_td_pts": 6.0,
    "receiving_yd_pts": 0.1,
    "reception_pts": 0.0,    # standard = no PPR
    "interception_pts": -2.0,
}


def parse_scoring_rules(
    raw_json: dict[str, Any],
) -> dict[str, Any]:
    """Parse MFL rules response into a structured scoring summary.

    Extracts key scoring parameters from the MFL positionRules structure.
    Returns a dict with the raw JSON plus extracted key parameters.
    """
    result: dict[str, Any] = {"raw": raw_json}
    key_rules: dict[str, float | None] = {}

    rules_root = raw_json.get("rules", {})
    position_rules = rules_root.get("positionRules", [])

    if isinstance(position_rules, dict):
        position_rules = [position_rules]

    # MFL event code -> our key name mapping
    event_map = {
        "#P": "passing_td_pts",
        "PY": "passing_yd_pts",
        "#R": "rushing_td_pts",
        "RY": "rushing_yd_pts",
        "#C": "receiving_td_pts",
        "CY": "receiving_yd_pts",
        "CC": "reception_pts",
        "IN": "interception_pts",
    }

    for pos_rule_group in position_rules:
        if not isinstance(pos_rule_group, dict):
            continue
        rules = pos_rule_group.get("rule", [])
        if isinstance(rules, dict):
            rules = [rules]

        for rule in rules:
            if not isinstance(rule, dict):
                continue
            event_code = ""
            points_str = ""

            event_obj = rule.get("event", {})
            if isinstance(event_obj, dict):
                event_code = str(event_obj.get("$t", "")).strip()
            elif isinstance(event_obj, str):
                event_code = event_obj.strip()

            points_obj = rule.get("points", {})
            if isinstance(points_obj, dict):
                points_str = str(points_obj.get("$t", "")).strip()
            elif isinstance(points_obj, str):
                points_str = points_obj.strip()

            if event_code in event_map and points_str:
                key_name = event_map[event_code]
                # Parse points value: "*6" means 6 per event, "*.05" means 0.05 per unit
                try:
                    cleaned = points_str.lstrip("*")
                    key_rules[key_name] = float(cleaned)
                except (ValueError, TypeError):
                    pass

        # Only need the first position group that has QB-relevant rules
        if key_rules:
            break

    result["key_rules"] = key_rules

    # Compute deviations from standard
    deviations: dict[str, str] = {}
    for key, standard_val in STANDARD_SCORING.items():
        actual = key_rules.get(key)
        if actual is not None and abs(actual - standard_val) > 0.001:
            deviations[key] = f"{actual} (standard: {standard_val})"

    result["deviations"] = deviations
    return result


def upsert_scoring_rules(
    db_path: str,
    league_id: str,
    season: int,
    parsed_rules: dict[str, Any],
) -> int:
    """Upsert scoring rules into league_scoring_rules table.

    Stores the full parsed result as JSON. Idempotent.
    Returns 1 on success, 0 on failure.
    """
    rules_json = json.dumps(parsed_rules, sort_keys=True, separators=(",", ":"))

    with DatabaseSession(db_path) as con:
        con.execute(
            """INSERT OR REPLACE INTO league_scoring_rules
               (league_id, season, rules_json)
               VALUES (?, ?, ?)""",
            (str(league_id), int(season), rules_json),
        )

    logger.info("Upserted scoring rules for league=%s season=%d", league_id, season)
    return 1


def ingest_scoring_rules_from_mfl(
    *,
    db_path: str,
    league_id: str,
    season: int,
    raw_json: dict[str, Any],
) -> int:
    """Full pipeline: parse MFL rules response and upsert into DB."""
    parsed = parse_scoring_rules(raw_json)
    if not parsed.get("key_rules"):
        logger.warning(
            "No scoring rules parsed for league=%s season=%d", league_id, season,
        )
        return 0
    return upsert_scoring_rules(db_path, league_id, season, parsed)
