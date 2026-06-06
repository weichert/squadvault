# Session Brief — Voice-Quality Calibration Pass (PFL Buddies)

**Date prepared:** 2026-06-06
**Session type:** Quality / calibration review. Does the now-live PFL voice produce recaps
that read as authentically PFL Buddies? Read + regenerate + assess. Produces a findings memo
and, if warranted, NUMBERED voice-refinement options for founder decision. **Diagnose only --
no voice rewrite without founder sign-off.**
**Engine HEAD at handoff:** e794575 (the status reconciliation + this brief land on top;
CONFIRM in verify-first).
**Repo:** `weichert/squadvault` -- local `~/projects/squadvault-ingest-fresh`.

---

## Why this session exists

The voice pipe is now closed end-to-end: PFL Buddies has a LIVE engine voice row
(`OBSERVATIONS_2026_06_05_PFL_VOICE_LIVE.md`), and recap generation injects it
(`creative_layer_v1.py`, `if voice_profile:`). "Voice-live demonstrated end-to-end" (2026-06-05)
proved the MECHANISM. No one has yet asked the Artisan-frame question: does the OUTPUT sound
like PFL Buddies? Per the status reconciliation
(`OBSERVATIONS_2026_06_06_PROJECT_STATUS_RECONCILIATION.md`), this is the highest-leverage,
on-mission, off-season-doable next move -- it returns focus from engine-mechanics/substrate to
the founder's-league experience, and it is the calibration-set work the north star names
(fantasy football as proving ground, not product).

This is not engine mechanics for its own sake. It is the "is it exquisite?" question the
Artisan frame puts first.

---

## Verify-first (mandatory)

    git log --oneline -6        # confirm HEAD e794575; status memo + this brief at top; tree clean
    git status

Then, before any regeneration:
1. Confirm the live voice row is real: read `OBSERVATIONS_2026_06_05_PFL_VOICE_LIVE.md`, and
   verify `get_voice_profile(db_path, "70985")` in `src/squadvault/core/tone/voice_profile_v1.py`
   returns the curated `profile_text` (NOT empty). If empty -> the pipe is not actually live and
   this session's premise is wrong; stop and report.
2. Confirm no prior voice-quality pass exists (grep `_observations/` -- none as of this brief).
   If one appears, read it first; do not re-run a closed pass.
3. Read the rubric the output is judged against: `PFL_Buddies_Voice_Profile_v1_0` (esp.
   section 5 "affectionate piling on" and section 6 "use the league's natural vocabulary
   where it emerges from the data, without forcing terms the system hasn't earned").

---

## The work (diagnostic-first per the dispatch model)

1. **Pick a representative 2025 sample.** The 7 validation-pass weeks from the Arc 1-3 closure
   span the range cleanly: W1, W4, W5, W8, W12, W13, W16/W17 (clean / FAAB-edited /
   ordinal-stat / streak / championship / blowout). Confirm each is regenerable
   (`scripts/recap_artifact_regenerate.py` is the established tool; the Arc 1-3 validation pass
   regenerated 7 weeks against the verifier stack, so this is a known operation).

2. **Regenerate each through the live voice (read-only to the ledger; regeneration only).**
   Capture the before (as-approved / default-tone) vs after (live PFL voice) pairs. Note: the
   facts and temporal-scoped context are unchanged -- only the voice directive differs -- so
   the verifier should still pass on the regenerated output. Any new verifier flag is itself a
   finding, not expected.

3. **Assess against the Voice Profile rubric.** For each week:
   - Does the voice LAND, or read as generic AI snark in costume? (we-construct, not me-construct.)
   - Does it use the league's natural vocabulary without forcing terms the data hasn't earned
     (section 6)?
   - Does the "affectionate piling on" (section 5) read as PFL Buddies specifically, or as
     generic ribbing?
   - Where does it nail it; where does it drift?

4. **STOP and report findings as a frame BEFORE any voice change.** The founding-session voice
   was commissioner-selected; re-tuning it is a founder call, not an in-session edit. This pass
   DIAGNOSES.

---

## Deliverable

- A findings memo `OBSERVATIONS_<date>_VOICE_QUALITY_CALIBRATION_PASS.md`: per-week
  assessment, the does-it-sound-like-PFL verdict, and (if warranted) NUMBERED voice-refinement
  options for founder decision -- proposed, not applied.
- Doc-only commit. Any regeneration is read-only to the ledger (facts immutable, append-only);
  regenerated artifacts are derived, never fact-creating.

---

## Scope boundaries (non-goals)

- **No voice rewrite without founder sign-off.** This pass diagnoses; it does not re-tune.
- **No ledger writes.** Regeneration only -- narratives derived, never fact-creating.
- **No analytics / engagement / optimization.** Voice-quality is voice-iteration data, not a
  metric (Operational Plan section 10 #4).
- **Not a 2026-season live run.** Off-season; no 2026 games until ~September. The 2025 recaps
  are the calibration set.
- **Manual-import and 2021 threads stay parked** (no clock).

---

## Stop-and-report checkpoints

- After verify-first: confirm the live voice row is non-empty and report HEAD + clean tree.
  If the voice row is empty, STOP -- the session premise fails.
- After assessment: report the verdict and any refinement options BEFORE changing the voice.

---

## One-line kickoff for the next session

> The voice pipe is live (PFL voice row installed, recaps inject it) but its OUTPUT was never
> reviewed. Regenerate a representative 2025 recap sample through the live PFL voice and assess
> against the Voice Profile rubric (we-construct not me-construct; affectionate piling-on;
> natural vocabulary): does it sound like PFL Buddies? Verify the live voice row is non-empty
> FIRST. Diagnose only -- numbered voice-refinement options for founder decision, no silent
> re-tune. Doc-only; ledger read-only.
