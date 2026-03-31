-- 0006_add_league_voice_profiles.sql
-- Adds commissioner-approved voice profiles for league-specific cultural guidance.
-- A voice profile is a richer, league-specific supplement to the tone preset.
-- It modulates expression but never creates facts, infers intent, or personalizes
-- to individuals. Commissioner approval gates activation.

CREATE TABLE IF NOT EXISTS league_voice_profiles (
  league_id     TEXT    NOT NULL,
  profile_text  TEXT    NOT NULL,
  approved_by   TEXT    NOT NULL DEFAULT 'commissioner',
  approved_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  PRIMARY KEY (league_id)
);
