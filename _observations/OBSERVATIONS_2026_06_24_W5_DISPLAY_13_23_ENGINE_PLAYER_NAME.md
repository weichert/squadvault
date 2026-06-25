# OBSERVATIONS 2026-06-24 - W.5 Display #13-23 (Option A) - ENGINE leg (detail.player_name)

**Lane:** EXECUTE (Part 1 of 2). **Engine:** from `74ac08a`. **Spec:**
`SquadVault_W5_Display_13_23_Specification_2026_06_24.md` (rev 2, Option A). Generator enrichment only - no
schema change, no migration. Frontend render + reseed is Part 2.

## What shipped (engine)
`gen_season_award_winners.py` now denormalizes the player name into the award row so the Trophy Room can
name the player, not just the franchise:
- `_load_season_player_names(db, lg, season)` - sibling of `_load_season_positions` over the same
  `player_directory.name` the engine already holds (recap/verifier consumers use it). Loaded once per season
  at the TOP of the season loop (the #3 Hammer emit precedes the Group C/D/E blocks, so the name map must be
  in scope before it).
- `detail["player_name"] = name_map.get(pid)` wherever a row names a SINGLE player: #3 The Hammer, the
  positional emit (#13-18), `_emit_pick_award` (#19/#20/#22), and #23 The Lifeline. Missing name -> key
  omitted (silence, never a guessed name). #21 (franchise-level, no player_id), #6 (player_ids only inside a
  list), #4/#12/#33/#7/#9 (no single player_id) are untouched.

## Determinism contract (proved - spec 4.0 / 7)
- Row count 256 -> 256; **0 fact-tuple violations**: every prior row's `(award_id, season, franchise_id,
  value)` byte-identical; `detail` minus `player_name` equals the prior detail exactly.
- `player_name` added to **154** rows == exactly the 154 rows carrying a `player_id` (100% resolution, and
  ONLY where a player_id exists). **#4/#12/#33 detail unchanged** (0 rows).
- Determinism: regenerate twice -> byte-identical. ruff / mypy / prove_ci green.

## All-time anchor names (spec 7 + the rest, for the frontend close-out)
- #13 Signal Caller 724.0/2011/0009 -> **Brees, Drew**.
- #22 The Whale $76 (co-hold): 2019/0002/13604 -> **Barkley, Saquon**; 2020/0002/13130 -> **McCaffrey,
  Christian** (season-correct names, distinct holders).
- #23 The Lifeline 352.00/2010/0006 -> **Vick, Michael**.
- (#14-18, #19-21 all-time holders + names to be reported in the Part 2 frontend close-out from the
  regenerated seed.)

## Prod-apply
The pending founder seed-004 hand-apply now targets the NAME-ENRICHED seed (regenerated in Part 2). Idempotent
DELETE+INSERT, so the enriched seed supersedes cleanly - the apply still happens once. NO prod write here.

## Guardrails
`player_name` is a denormalized fact (`player_directory.name`), not invented - the project's promote-at-ingest,
read-canonical pattern. The `player_directory` read is generator-local in `scripts/` (the existing position
read already is; the src/-only check_no_memory_reads gate is unaffected). Silence over speculation (missing
name omits the key). No ranking/leaderboard.
