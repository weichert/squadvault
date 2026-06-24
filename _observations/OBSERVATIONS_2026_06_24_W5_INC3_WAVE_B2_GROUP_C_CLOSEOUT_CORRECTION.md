# OBSERVATIONS 2026-06-24 - W.5 Inc 3 Wave B2 Group C CLOSE-OUT - CORRECTION

**Corrects:** `OBSERVATIONS_2026_06_24_W5_INC3_WAVE_B2_GROUP_C_CLOSEOUT.md` (committed engine `8713319`).
**Type:** clerical (new dated memo per Charter section 6 - observation memos are not edited after commit).

**Correction.** The close-out's "Coverage ledger" line names the single Group C same-season co-holder tie as
"#17 PK **2017**". The correct season is **2011**: award #17 (The Boot, PK) has two cross-franchise co-holders
in 2011 - franchise `0004` (player `1383`) and `0005` (player `8742`), each at 131.0 started points. 2017 PK
has a single holder.

**Unchanged.** The substantive finding holds exactly as recorded: Group C emits 97 rows (96 covered
position-seasons + one cross-franchise co-holder tie at #17 PK), 0 unique-key violations, 0 silence-rendered.
Only the year label was wrong. The prod-apply proof block (frontend `champ_week_correction_and_b2_awards_probes.sql`
section 3c) carries the correct 2011 tie.
