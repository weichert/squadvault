-- 0004_add_league_tone_profiles.sql
-- Adds the league_tone_profiles table for commissioner-configured voice presets.

CREATE TABLE IF NOT EXISTS league_tone_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  league_id TEXT NOT NULL,
  tone_preset TEXT NOT NULL CHECK (tone_preset IN ('TRASH_TALK', 'POINTED', 'BALANCED', 'FRIENDLY')),
  set_by TEXT NOT NULL DEFAULT 'commissioner',
  notes TEXT,
  created_at TEXT NOT NULL,
  UNIQUE (league_id)
);
