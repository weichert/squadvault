-- scripts/seed_pfl_buddies_nicknames.sql
--
-- Commissioner-curated PFL Buddies (league_id 70985) nickname seeds.
-- Consumed by _build_reverse_name_map pass 4a (per commit 84bfd89).
-- Persistence gives the verifier a stable anchor against owner_name
-- drift from the upstream MFL adapter.
--
-- Not a migration: this is operational seed data, not schema DDL.
-- The schema mechanism shipped in 84bfd89 (migration 0010); this
-- script populates the content that makes pass 4a active for this
-- league. Run intentionally by the commissioner; do not wire into
-- the migration runner.
--
-- Idempotent: re-running preserves curated_at from the initial
-- curation and only bumps updated_at. Re-applies the nickname value
-- in case the commissioner has edited it upstream.
--
-- Usage:
--   sqlite3 .local_squadvault.sqlite < scripts/seed_pfl_buddies_nicknames.sql
--
-- Verification after apply:
--   sqlite3 .local_squadvault.sqlite \
--     "SELECT franchise_id, nickname FROM franchise_nicknames
--      WHERE league_id='70985' ORDER BY franchise_id;"
--   -- Expect: 10 rows matching the values below.

INSERT INTO franchise_nicknames (league_id, franchise_id, nickname)
VALUES
  ('70985', '0001', 'Stu'),
  ('70985', '0002', 'KP'),
  ('70985', '0003', 'Pat'),
  ('70985', '0004', 'Eddie'),
  ('70985', '0005', 'Steve'),
  ('70985', '0006', 'Miller'),
  ('70985', '0007', 'Robb'),
  ('70985', '0008', 'Ben'),
  ('70985', '0009', 'Michele'),
  ('70985', '0010', 'Brandon')
ON CONFLICT(league_id, franchise_id) DO UPDATE SET
  nickname = excluded.nickname,
  updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now');
