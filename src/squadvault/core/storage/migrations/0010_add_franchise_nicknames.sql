-- 0010_add_franchise_nicknames.sql
-- Adds commissioner-curated league-used short-forms keyed by
-- (league_id, franchise_id). Cross-season: a single nickname row
-- applies across every season that franchise exists in this league.
--
-- Consumed by _build_reverse_name_map pass 4a (ahead of pass 4b's
-- owner-first-word extraction) to resolve franchise references the
-- league writes in insider voice but that neither the franchise name
-- nor the owner's first name would surface — the canonical example
-- being "KP" for Paradis' Playmakers in PFL Buddies.
--
-- Commissioner approval gates curation; empty table is the normal
-- pre-curation state. Never creates facts; only modulates alias
-- derivation for verifier name-matching.

CREATE TABLE IF NOT EXISTS franchise_nicknames (
  league_id     TEXT    NOT NULL,
  franchise_id  TEXT    NOT NULL,
  nickname      TEXT    NOT NULL,
  curated_by    TEXT    NOT NULL DEFAULT 'commissioner',
  curated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

  PRIMARY KEY (league_id, franchise_id)
);
