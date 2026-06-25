# OBSERVATIONS 2026-06-24 - W.5 #23 The Lifeline - skill-position floor (FACT layer)

**Lane:** EXECUTE (Part 1 of 2). **Engine:** from `b47254d`. Founder ruling 2026-06-24: the Lifeline should
read as a triumphant skill pickup - exclude kickers and defenses. FACT-layer change (engine #23 redefinition
-> reseed -> founder re-apply). The name-format change is the paired RENDER-layer frontend unit. No schema.

## Change
`gen_season_award_winners.py`: #23 candidate selection now keeps only acquired players whose
`player_directory` position is in `LIFELINE_SKILL_POSITIONS = (QB, RB, WR, TE)` - `PK` and `Def` excluded.
Everything else about #23 is unchanged (in-season acquisition channels, per-franchise, regular-season started
points, floor `starter_weeks >= 4`, all 16 seasons, week-floor dropped). Reuses the already-loaded `pos_map`
(no new data source). #17 The Boot (PK) and #18 The Wall (Def) are untouched - the intentional kicker/defense
awards.

## Census (re-derived BEFORE merge)
Exactly four seasons had a non-skill winner and change; each STILL has a qualifying skill acquisition clearing
the `>= 4` floor (NO season silences):
- 2014: Vinatieri (PK) -> **0010/11232 DeAndre Hopkins (WR) 108.0**, 7 starts.
- 2018: Crosby (PK) -> **0001/13614 Phillip Lindsay (RB) 99.2**, 6 starts.
- 2019: New England (Def) -> **0001/13671 Mark Andrews (TE) 115.0**, 11 starts.
- 2022: Bass (PK) -> **0009/13139 Jamaal Williams (RB) 81.6**, 8 starts.

## Determinism contract (proved)
- Row count **256 -> 256** (no silences). Awards #4/#12/#33 and #13-#22 **byte-identical** (facts untouched).
- #23 changes ONLY the four seasons above; the other 12 #23 rows byte-identical.
- All-time #23 face unchanged: **Vick, 352.00, 2010, 0006** (QB).
- Zero non-skill (PK/Def) rows remain in #23.
- ruff / mypy / prove_ci green.

## Prod-apply (FOUNDER-gated; NO prod write)
Seed 004 regenerated in Part 2 (frontend); the founder re-applies the same idempotent
`BEGIN; DELETE ... award_id IN (...); INSERT ...; COMMIT;` - it supersedes the current rows, only #23 differs.
Post-apply: the four upgraded seasons show skill-position players. Names in the seed/detail stay canonical
"Last, First" (the RENDER layer formats to "First Last" - Part 2).

## Guardrails
Retrospective fact (skill production of completed-season pickups). Silence over speculation (a season with no
skill acquisition over the floor would drop a row - none do today). No analytics/optimization/prediction.
Tone-care neutral. The position is `player_directory` canonical - not invented.
