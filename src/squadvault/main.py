from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from squadvault.config import load_config
from squadvault.mfl.client import MflClient
from squadvault.notion.client import NotionClient
from squadvault.notion.schema_specs import build_schema_specs
from squadvault.notion.schema_validator import validate_all_databases
from squadvault.ingest.transactions import ingest_transactions_for_year


def _parse_years(value: str) -> list[int]:
    value = value.strip()
    if not value:
        return []
    parts = [p.strip() for p in value.split(",") if p.strip()]
    years: list[int] = []
    for p in parts:
        years.append(int(p))
    return years


def _setup_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _preflight() -> None:
    """Print runtime environment info for debugging path issues."""
    cwd = Path.cwd().resolve()
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent  # src/squadvault -> src -> repo_root

    logger = logging.getLogger("squadvault.preflight")
    logger.info("Working directory: %s", cwd)
    logger.info("Repo root (inferred): %s", repo_root)
    logger.info("Script location: %s", script_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="squadvault-ingest")
    parser.add_argument("--validate-only", action="store_true", help="Validate Notion schemas only; do not ingest.")
    parser.add_argument("--years", type=str, default="", help="Comma-separated years to ingest, e.g. 2024 or 2020,2021.")
    args = parser.parse_args(argv)

    cfg = load_config()
    _setup_logging(cfg.log_level)
    _preflight()

    notion = NotionClient(api_key=cfg.notion_api_key, notion_version=cfg.notion_version)
    mfl = MflClient(
        server=cfg.mfl_server,
        league_id=cfg.mfl_league_id,
        username=cfg.mfl_username,
        password=cfg.mfl_password,
    )

    specs = build_schema_specs(cfg)

    # Always validate first (hard-fail if mismatch).
    validate_all_databases(notion=notion, specs=specs)

    if args.validate_only:
        print("Schema validation passed for all configured databases. (--validate-only; no ingestion performed)")
        return 0

    years = _parse_years(args.years)
    if not years:
        print("No years provided. Use --years 2024 (or comma-separated list).", file=sys.stderr)
        return 2

    for year in years:
        logging.getLogger("squadvault.main").info("Ingesting year=%s", year)
        ingest_transactions_for_year(cfg=cfg, notion=notion, mfl=mfl, year=year)

    print("Ingestion complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
