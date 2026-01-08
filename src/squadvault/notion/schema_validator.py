from __future__ import annotations

import logging
from typing import Any, Dict

from squadvault.notion.client import NotionClient
from squadvault.notion.schema_specs import DatabaseSpec

logger = logging.getLogger(__name__)


def _fail(msg: str) -> None:
    raise RuntimeError(msg)


def _get_prop(db_json: Dict[str, Any], prop_name: str) -> Dict[str, Any] | None:
    props = db_json.get("properties", {})
    return props.get(prop_name)


def _notion_type(prop_json: Dict[str, Any]) -> str:
    return prop_json.get("type", "")


def _normalize_uuid(uuid_str: str | None) -> str:
    """Remove hyphens from UUID for consistent comparison."""
    if uuid_str is None:
        return ""
    return uuid_str.replace("-", "").lower()


def _validate_relation_target(prop_json: Dict[str, Any], expected_target_db_id: str) -> None:
    rel = prop_json.get("relation") or {}
    actual_target = rel.get("database_id")
    if _normalize_uuid(actual_target) != _normalize_uuid(expected_target_db_id):
        _fail(f"Relation target mismatch: expected={expected_target_db_id} actual={actual_target}")


def validate_database(notion: NotionClient, name: str, spec: DatabaseSpec) -> None:
    db_json = notion.get_database(spec.database_id)

    # Title property exists and is type title.
    title_prop = _get_prop(db_json, spec.title_property)
    if not title_prop:
        _fail(f"[{name}] Missing title property '{spec.title_property}' in database {spec.database_id}")
    if _notion_type(title_prop) != "title":
        _fail(f"[{name}] Title property '{spec.title_property}' is not type 'title' (actual={_notion_type(title_prop)})")

    for prop_name, prop_spec in spec.required_properties.items():
        prop_json = _get_prop(db_json, prop_name)
        if not prop_json:
            _fail(f"[{name}] Missing required property '{prop_name}' in database {spec.database_id}")

        actual_type = _notion_type(prop_json)
        expected_type = prop_spec.notion_type
        if actual_type != expected_type:
            _fail(
                f"[{name}] Property type mismatch for '{prop_name}': expected={expected_type} actual={actual_type}"
            )

        if expected_type == "relation" and prop_spec.relation is not None:
            _validate_relation_target(prop_json, prop_spec.relation.target_database_id)

    logger.info("Schema OK: %s (%s)", name, spec.database_id)


EXPECTED_DATABASE_NAMES = frozenset([
    "Seasons",
    "Weeks",
    "Franchise Season",
    "Weekly Team Results",
    "Matchups",
    "MFL API Inventory",
    "Transactions",
    "Waiver Bids",
    "Auction Draft Results",
])


def validate_all_databases(notion: NotionClient, specs: Dict[str, DatabaseSpec]) -> None:
    logger.info("Validating Notion schemas for %d databases...", len(specs))

    # Verify all 9 expected databases are present in specs
    provided_names = set(specs.keys())
    missing = EXPECTED_DATABASE_NAMES - provided_names
    if missing:
        _fail(f"Schema specs missing required databases: {sorted(missing)}")

    extra = provided_names - EXPECTED_DATABASE_NAMES
    if extra:
        logger.warning("Extra databases in specs (not expected): %s", sorted(extra))

    for name, spec in specs.items():
        validate_database(notion=notion, name=name, spec=spec)

    logger.info("All %d Notion schema validations passed.", len(specs))
