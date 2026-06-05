# Founding Voice Does Not Reach Recap Generation -- Frontend/Engine Voice Systems Are Unconnected

**Date:** 2026-06-04
**Status:** Observational. No tier. Not registered in the Documentation Map.
**Repos:** frontend `weichert/squadvault-frontend` (HEAD d876d84); engine `weichert/squadvault` (HEAD 7532c25).
**Trigger:** Closing out F-4 (founding-session edge cases) in the frontend, a tracked follow-on asked whether the engine resolves a null `voice_profile_id` to MIXED at recap time. Grounding the engine to answer it found the premise was wrong: the engine never reads that field. This memo records the actual finding so the follow-on is replaced by the real gap.

---

## 1. Two voice systems, no bridge

**Frontend (Supabase).** The founding session writes a `voice_profiles` row (`profile_key` from the calibration cards, e.g. BALL_BUSTING_FRIENDS, plus generated `prose`) and points `leagues.voice_profile_id` at it. On skip (spec 9.1) `voice_profile_id` is left null; MIXED is the default at the frontend's own founding generate path (`?? 'MIXED'`).

**Engine (SQLite).** Recap generation resolves voice via `get_voice_profile(db_path, league_id)` in `src/squadvault/core/tone/voice_profile_v1.py`, reading a `profile_text` from its own `league_voice_profiles` table. The creative layer (`src/squadvault/ai/creative_layer_v1.py`) injects it only when present (`if voice_profile:`); absent -> no voice directive, default tone preset. `set_voice_profile` has no automated callers in the engine; PFL Buddies' engine voice was populated separately by the Phase 10 chat-export analysis.

**The gap.** Nothing connects the two. `voice_profile_id` appears nowhere in the engine, and there is no Supabase-to-engine voice flow. A commissioner's founding voice selection does not currently reach recap generation.

## 2. Why this is safe today (not urgent)

- The original follow-on ("engine should default null voice_profile_id to MIXED") is **not applicable**: the engine does not consult that field, so a skipped league's null is inert engine-side.
- Absent voice is already handled gracefully engine-side (empty -> no directive -> default tone preset). No crash, no fabrication; silence-over-speculation holds.
- The only real league with recaps (PFL Buddies) has its engine voice set separately, so it is unaffected.
- New leagues founded through the frontend have no engine recaps until a season runs, so none is in the gap today.

## 3. The decision this implies (when picked up)

Whether and how founding-authored voice should flow to the engine's `league_voice_profiles`. Open questions for that design pass:

- **Mapping.** The frontend stores a register *key* plus prose; the engine stores a `profile_text`. A bridge must decide what `profile_text` corresponds to each key, and what MIXED (the skip / first-year-uncertain default) maps to engine-side.
- **Direction and mechanism.** The existing sync is engine-to-Supabase (recaps up). A voice bridge is the reverse (Supabase-to-engine), a new flow with its own idempotency and trigger point.
- **Authority.** Both systems already gate voice on commissioner approval; a bridge must preserve "commissioner approves before it affects output."

## 4. Scope

Pre-existing; not introduced by F-4; not a regression. No code in this session. Deferred until the voice bridge is deliberately designed. Frontend follow-on item 1 is reframed from "verify null-to-MIXED" to "this gap," and can otherwise be dropped.
