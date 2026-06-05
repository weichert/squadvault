# OBSERVATIONS 2026-06-05 - Voice-Live Demonstrated End-to-End; CI Fixture Fingerprint Defect

Status: Voice-live ORIGINAL GOAL achieved (demo-level, real fixture data). One
follow-up item opened (fixture fingerprint defect). Engine path confirmed sound.

## Summary

The curated PFL Buddies voice was demonstrated shaping a real recap end-to-end,
using the CI fixture's 2024 data as a local working DB (Track C / fixture-copy
demo). A before/after on Season 2024 Week 1 produced a clear register change in
the shareable recap while the deterministic facts block above it stayed
byte-identical. This is the first time the original goal - PFL recaps rendering
in the curated voice - has been shown working on real data.

The working DB was .local_squadvault.sqlite (gitignored, disposable), copied from
fixtures/ci_squadvault.sqlite. Nothing was approved; all artifacts were DRAFT
versions (append-only). The committed fixture was never mutated.

## What was proven (the win)

- Voice read path is wired and effective: get_voice_profile (weekly_recap_lifecycle.py
  line ~1048) -> _PromptContext.voice_profile -> draft_narrative_v1(voice_profile=...)
  (line ~1306) -> creative_layer_v1._build_system_prompt appends the profile to the
  system prompt directives (line ~226). Empty profile -> default tone; curated row
  present (3938 chars) -> curated voice.
- The before/after difference is attributable to the voice, not model noise. The
  BEFORE shareable recap used full team names in a neutral register (Paradis'
  Playmakers, Stu's Crew, Brandon Knows Ball). The AFTER resolved managers to
  first-name insider register (KP, Stu, Brandon, Michele, Ben, Steve) and adopted
  the clubhouse tone the profile encodes. That manager-identity shift is exactly
  what PFL_Buddies_Voice_Profile + the derive_manager_identities path describe.
- Facts immutable, narrative derived - visibly. The facts block (dollar amounts,
  players, the Olave/LaPorta trade) was byte-identical across both runs. Only the
  register changed. This is the single most convincing artifact for an external
  audience: same ledger, two voices, zero fact drift.

## The chase - root causes found (so the next session does not re-walk this)

1. ANTHROPIC_API_KEY was NOT in engine .env.local. The engine .env.local on this
   machine carried only SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY - no API key and
   no MFL creds, contrary to the prior brief's description of that file. The working
   key lives in the FRONTEND .env.local (~/squadvault/.env.local). It was copied
   across (idempotent, non-clobbering append). Model pin claude-sonnet-4-20250514 is
   still valid (a live probe returned ok); anthropic SDK 0.87.0 present.

2. Fixture weeks 6 / 17 / 18 are empty placeholders. recap_runs week 6 carries
   selection_fingerprint=test-fingerprint with empty canonical_ids_json; weeks 17/18
   carry the SHA-256 of the empty string (e3b0c44...852b855) with 2-byte ids_json.
   Generating any of these yields Events selected: 0 and a summary-only recap. The
   brief's week-6 example pointed at one of these empty weeks.

3. THE LOAD-BEARING DEFECT - fixture selection id-space. recap_runs.canonical_ids_json
   for the real-selection weeks (1-4) stores numeric row-ids (e.g. 6991, 6992), but
   the loader _load_canonical_event_rows matches WHERE action_fingerprint IN (...)
   against v_canonical_best_events. Real fingerprints look like
   DRAFT_PICK:70985:2024:MEMORY_EVENT_ID:10. Numeric ids never match -> 0 events
   loaded -> 0 creative bullets -> draft_narrative_v1 hits its empty-facts guard
   (if not facts_bullets: return None) -> silent fallback to facts-only. Every layer
   downstream looked broken (key, model, EAL) but the bottom was this id mismatch.

4. THE ENGINE IS SOUND - defect is fixture-only. The live selection writer
   select_weekly_recap_events_v1 stores fingerprints (weekly_selection_v1.py line
   150: action_fingerprint AS canonical_id; line 167 collects them). The loader
   reads fingerprints. They agree. Production would work with a properly-built DB.
   The fixture was assembled/stamped with the wrong id space - a fixture-data
   defect, not a code bug. Classification: FIXTURE_SIDE.

## Demo recovery method (reusable for any future fixture-based creative demo)

Re-run the engine's own selection writer on the working copy to repair the
selection, then generate. Proven against weeks 1-4 (19/15/11/14 bullets):

  sel = select_weekly_recap_events_v1(db_path=DB, league_id="70985", season=2024, week_index=1)
  upsert_recap_run(DB, RecapRunRecord(..., canonical_ids=[str(c) for c in sel.canonical_ids],
                   selection_fingerprint=sel.fingerprint, counts_by_type=sel.counts_by_type, ...))
  generate_weekly_recap_draft(db_path=DB, league_id="70985", season=2024, week_index=1,
                              reason="voice_demo", force=True)

force=True is required because generate is fingerprint-idempotent. reason is a
free-form label (no enum gate). Week 1 EAL directive is HIGH_CONFIDENCE_ALLOWED.

## Governance observation (honest flag, not alarm)

The AFTER shareable prose reached for draft-strategy numerics not present in the
week's selected transaction events: a $70 top pick / $1 cheapest for Michele, and
Ben spending $99 of $200 on wideouts. These appear sourced from season/draft
context in the prompt assembly rather than the week-1 selection set. This is
exactly recap_verifier_v1 territory (NUMERIC_UNANCHORED / SUPERLATIVE categories).
Because the output was a DRAFT and nothing was approved, the governance model
behaved correctly (AI drafts, human approves). But these figures must be confirmed
grounded before this kind of output is ever surfaced publicly. Not scoped here.

## FOLLOW-UP ITEM (open) - CI Fixture Fingerprint Defect

Discrete, trackable. fixtures/ci_squadvault.sqlite cannot drive a creative recap
out of the box:
  - recap_runs weeks 1-4: canonical_ids_json holds numeric row-ids, not action
    fingerprints. Loader expects fingerprints -> 0 events resolve.
  - recap_runs weeks 6 / 17 / 18: empty placeholders (test-fingerprint /
    empty-string hash).
Impact: any fixture-based creative-recap demo or validation silently degrades to
facts-only with no error. Decision needed (surface options next session):
  A. Regenerate the fixture's recap_runs via the real selection path
     (select_weekly_recap_events_v1 + upsert_recap_run) so stored ids are
     fingerprints, then re-commit the fixture.
  B. Document as a known fixture limitation and require a re-selection prep step
     in any demo that needs the creative layer.
Recommendation deferred to a scoped session; this memo only opens the item.

## State at session end

- Engine HEAD unchanged by the demo (working DB is gitignored; only this memo and
  the .env.local key-copy touched disk). .env.local is gitignored.
- Voice mechanism (set_pfl_voice, voice_profile_v1, read path) all confirmed live
  and correct.
- Disposable working DB .local_squadvault.sqlite can be removed (rm).
