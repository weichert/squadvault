# reverse_name_map owner-alias uniqueness diagnostic — PFL Buddies 2024, 2025

**Commit:** 67c5707 (underlying verifier code unchanged from 07d752b;
SHA of `recap_verifier_v1.py`: `745d1f8a…`)
**Corpus:** `franchise_directory` rows for `(league_id=70985,
season ∈ {2024, 2025})`
**Harness:** `/tmp/diagnose_reverse_name_map.py`
**Trace output:** `/tmp/sv_reverse_name_map_diagnostic/`
**Status:** FINAL

---

## Headline finding

**`franchise_directory.owner_name` is empty for every PFL Buddies
franchise in both 2024 and 2025.** `_load_franchise_owner_names`
returns an empty dict for each season. Pass 4 of
`_build_reverse_name_map`, which creates owner first-name aliases, is
gated on `if owner_map:` and is therefore **never executed** for this
league at 67c5707.

Every owner-nickname resolution the 2026-04-20 APPROVED_STREAK_PROSE_
CLASSIFICATION memo investigated (`pat`, `steve`, `kp`, `michele`) is
absent via the same single mechanism: **"never considered."** There are
no uniqueness drops, no length-threshold skips, no stopword hits — just
the complete absence of the data feeding pass 4.

This is a data-layer absence, not a verifier-code defect. The 04-20
memo's HAZARD_A classification for F1/F2/F3 is correct at the verifier
layer but points one level too high; the upstream cause for all three
misattributions is empty `franchise_directory.owner_name`.

---

## Results

### Season 2024

- Franchises loaded: **10**
- Owners loaded: **0** (none of the 10 franchises have a populated
  `owner_name` field for season 2024)
- Final map size: **35 aliases** (from passes 1, 2, 3 only; pass 4
  dormant)

### Season 2025

- Franchises loaded: **10**
- Owners loaded: **0** (same absence as 2024)
- Final map size: **35 aliases**

### Names-of-interest resolution

Cross-season matrix (both seasons identical since both lack owner data):

| name | 2024 | 2025 | mechanism |
|---|---|---|---|
| `pat` | absent | absent | never considered (no owner_name data → pass 4 dormant) |
| `steve` | absent | absent | never considered (same) |
| `kp` | absent | absent | never considered (same) |
| `michele` | absent | absent | never considered (same) |
| `ben` | → Ben's Gods | → Ben's Gods | pass 2 (first-word of franchise name) |
| `brandon` | → Brandon Knows Ball | → Brandon Knows Ball | pass 2 |
| `robb` | → Robb's Raiders | → Robb's Raiders | pass 2 |
| `stu` | → Stu's Crew | → Stu's Crew | pass 2 |
| `miller` | → Miller's Genuine Draft | → Miller's Genuine Draft | pass 2 |
| `paradis` | → Paradis' Playmakers | → Paradis' Playmakers | pass 2 |
| `weichert` | → Weichert's Warmongers | → Weichert's Warmongers | pass 2 |

Every currently-resolving name in the name-of-interest set is mapped
via pass 2 (franchise name decomposition). **None via pass 4.** When a
franchise's owner uses a short-form that does not appear in the
franchise name itself (Michele for Italian Cavallini, Pat for Purple
Haze, KP for Paradis' Playmakers, Steve for Weichert's Warmongers —
and likely the owners of the two franchises not covered in the names-
of-interest list), the verifier's attribution pipeline cannot resolve
that short-form at all.

### Pass-4 dormancy — structural consequences

Without pass 4 active:

- Owner first names used in prose resolve only incidentally — if they
  happen to coincide with a franchise first-word (e.g., "Miller" as
  both franchise first-word and an owner first name). None of PFL
  Buddies' named owners in this diagnostic appear to coincide this way
  except by accident.
- Proximity-based `_find_nearby_franchise` falls back to whatever
  other aliases are in the window. In all three approved-corpus
  MISATTRIBUTION cases from the 04-20 memo (F1, F2, F3), proximity
  snagged a different franchise's alias — once on a word-boundary
  franchise name (Miller in F1, Robb in F2) and once on a substring
  hazard ("ben" in "bench" in F3).
- Brief #1 (`_POSSESSIVE_OBJECT_WIN_STREAK`) still produces correct
  attribution *iff* the possessor is mappable. With pass 4 dormant,
  possessors that are owner first names are NOT mappable, so Brief #1
  would fall through to unmappable-possessor silence rather than
  correct attribution. Outcome is still preferable to misattribution
  (silence over speculation), but neither brief delivers a positive
  attribution for owner-named possessors until pass 4 is active.

---

## Confirmation matrix against 2026-04-20 memo

| 04-20 failure | 04-20 hazard framing | Diagnostic reframing |
|---|---|---|
| F1 (2024 W4, Miller 3-game, prose: "Michele's...three-game win streak") | HAZARD_A possessive-of-noun | Would resolve with `michele` mapped via pass 4; populate owner_name. Brief #1 becomes a secondary hardening once pass 4 is active. |
| F2 (2024 W5, Robb 4-game, prose: "Michele's now won four straight") | HAZARD_A subject-of-verb variant | Would resolve with `michele` mapped via pass 4; proximity pass-1 would prefer `michele` (rightmost, just before match) over `robb`. The subject-of-verb structural concern becomes a theoretical robustness issue, not an active defect — no verbal-construction regex needed if pass 4 provides the possessor alias via adjacent-word proximity. |
| F3 (2024 W7, Ben 5-game, prose: "Pat's five-game win streak") | HAZARD_A + HAZARD_B compound (substring "ben" in "bench") | Would resolve with `pat` mapped via pass 4. `pat` at word-boundary "Pat's" sits rightmost, beats "bench" substring regardless of Brief #2 ever shipping. |
| F4 (2024 W9 Ben 4-game) | LEGITIMATE_CATCH | Unchanged — model-side error, correctly attributed. |
| F5 (2025 W5 Stu 4-game losing) | LEGITIMATE_CATCH | Unchanged — model-side error, correctly attributed via name match. |
| F6 (2025 W16 Warmongers 3-game) | LEGITIMATE_CATCH | Unchanged — attribution fragile (pass-2 via "warmongers") but the catch itself is model-side. Would attribute via pass-1 once `steve` is mapped. |
| F6 cross-week artifact (KP 5-game misattributed to Warmongers) | attribution bleed-through | Would resolve with `kp` mapped via pass 4 — if owner_name population uses the short-form "KP" rather than the legal first name "Kevin". This is a curation choice for the population pass. |

All three 04-20 MISATTRIBUTION entries + the F6 cross-week artifact
resolve from a single data-layer change. The 04-20 memo's Brief #1 and
Brief #2 both retain value as code-layer hardening but are no longer
near-term blockers on the approved-corpus failure set.

---

## Brief #1 / Brief #2 status reconsideration

Previous (04-20 memo) priority:
1. Brief #1 widened scope decision
2. Brief #1 implementation
3. Brief #2 defense-in-depth

Reconsidered priority (this memo):

1. **Owner-name population curation pass** (new, highest-value).
   Characterize what `owner_name` values should be per franchise —
   specifically, which short-form the league uses in insider-voice
   prose per franchise (Michele vs Michele Cavallini vs "M", KP vs
   Kevin, etc.). This is a curation task requiring human judgment;
   cannot be automated.
2. **Owner-name population itself.** DB update against
   `franchise_directory.owner_name`, ideally via the ingest path
   (per the MFL adapter contract; don't hand-patch the DB if an
   ingest path exists and MFL exposes the data).
3. **Re-run the diagnostic** post-population to confirm pass 4
   activates, all expected aliases resolve, and no new uniqueness
   collisions appear.
4. **Re-run `verify_season.py`** against the approved corpus to
   observe which of the 6 STREAK failures and 2 cross-week flags
   resolve. Expected: F1, F2, F3 resolve; F6's same-week artifact
   resolves; F4, F5, F6-primary remain as LEGITIMATE_CATCH (model
   errors to surface for human review).
5. **Brief #1 scope decision** — only if residual failures exist
   post-population that a code-layer fix would address. If
   population resolves everything the 04-20 memo flagged, Brief #1
   becomes a lower-priority hardening rather than a near-term
   implementation target.

Brief #2 priority is unchanged (remains defense-in-depth against
substring proximity hazards; independently useful but no F3 urgency
once population lands).

---

## Curation considerations for the population pass (not this pass)

This diagnostic does not decide the population strategy; it only
characterizes the current state. However, two considerations surface
from the data that are worth capturing for the next session's brief:

- **MFL ingest vs manual curation.** The MFL platform adapter may or
  may not expose an `owner_name` field in the raw payload. If it does,
  populating owner_name should route through the ingest path, not a
  manual DB update, to preserve the append-only / ingest-canonical
  contract. Confirm during the population-pass pre-read by inspecting
  the MFL owner payload schema and any ingest-side handling already
  in place.

- **Legal name vs league-used name.** Pass 4 takes `words[0].lower()`
  of `owner_name`. If Paradis' Playmakers' MFL-reported owner is
  "Kevin Paradis", pass 4 creates alias `kevin`, not `kp`. If the
  league prose never uses "Kevin", that alias is dead. The curation
  choice is whether to (a) populate with MFL-reported legal name and
  accept some dead aliases, (b) override with league-used first name /
  nickname in `owner_name`, (c) add a separate column for nicknames
  and widen pass 4 to consider both. Option (c) is a code change
  outside the scope of a pure population pass.

This is decision-making territory for the population-pass brief, not
for this diagnostic.

---

## Out of scope (what this pass did NOT do)

- populate `franchise_directory.owner_name`
- propose a specific per-franchise name/nickname mapping
- propose changes to the pass-4 aliasing logic (length thresholds,
  stopword list, uniqueness handling)
- propose changes to `franchise_directory` schema (e.g., adding an
  `owner_nickname` column)
- touch Brief #1 or Brief #2 scope decisions beyond reprioritization
  relative to the owner-name population pass
- re-run `verify_season.py` against the approved corpus (which would
  only reproduce the 6 failures the 04-20 memo already classified,
  since this pass made no changes)

All such work is captured as separate backlog items above.

---

## Addendum note for 2026-04-20 APPROVED_STREAK_PROSE_CLASSIFICATION memo

That memo's "New brief candidate — owner-alias uniqueness diagnostic"
section accurately predicted the diagnostic as a valuable next pass,
but hypothesized pass-4 uniqueness-collision drops as the mechanism.
The actual mechanism is more basic: pass 4 never runs because
owner_map is empty. The 04-20 memo's per-failure classifications
(MISATTRIBUTION / LEGITIMATE_CATCH) remain correct; the hazard-class
framing (HAZARD_A) is correct at the verifier-code layer; the missing
context was that the upstream data layer is also unpopulated.

No amendment to the 04-20 memo required — it cross-references this
memo by date and the reader will follow the trail. Future session
briefs citing the 04-20 memo should include this memo as a mandatory
pre-read when Brief #1 comes up for implementation.
