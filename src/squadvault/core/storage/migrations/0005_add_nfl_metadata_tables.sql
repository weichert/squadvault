-- 0005_add_nfl_metadata_tables.sql
-- Adds metadata tables for NFL bye weeks and league scoring rules.
-- These are reference data (like player_directory and franchise_directory),
-- not canonical events. They support Dimension 10 (bye week angles) and
-- Dimension 11 (scoring rules context) of Narrative Angles v2.

CREATE TABLE IF NOT EXISTS nfl_bye_weeks (
  league_id   TEXT    NOT NULL,
  season      INTEGER NOT NULL,
  nfl_team    TEXT    NOT NULL,
  bye_week    INTEGER NOT NULL,

  updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  PRIMARY KEY (league_id, season, nfl_team)
);

CREATE TABLE IF NOT EXISTS league_scoring_rules (
  league_id   TEXT    NOT NULL,
  season      INTEGER NOT NULL,
  rules_json  TEXT    NOT NULL,

  updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  PRIMARY KEY (league_id, season)
);
