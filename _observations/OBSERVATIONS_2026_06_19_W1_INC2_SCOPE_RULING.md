# OBSERVATIONS 2026-06-19 - Phase 11 W.1 Increment 2 SCOPE RULING (member captions in the A/V Room)

**Session type:** DECIDE (Charter rhythm). W.1 is SAT-admitted (exercise 1, discharged at Inc 1);
this is an INCREMENT scope ruling, not a fresh admission - the lighter chain (scope ruling +
increment spec, Opus build). Captions are governed-testimony-class, so the constitutional weight is
real even though the surface is admitted. Founder sole adjudicator. Append-only; supersedes nothing
except the one DoR attribution recorded below.

**Anchors VERIFIED this session (git, not brief):** engine main 8a90e62, frontend main 73833bc;
both main-only (the feat/l1-historian-capture branch is already tag-and-deleted - not present on
either remote, correcting the brief's "may still be present" note). Prod parity confirmed by
object-existence probe on qcaxemuydxlzpzgnnnoa: media_entries, media_provenance_tag_events,
media_display_withdrawals (Inc 1 / migration 011), member_consent_events (W.6 / 010),
member_history_exchanges (L.1 / 020), and testimony_separation_probe() (L.1 / 021) all present
(six-true). Repo == prod at 021; safe to scope a 022 caption migration.

**Reuse sources read this session:** 011_w1_av_room (the substrate captions attach to);
010_member_consent_events (the W.6 consent log + derived view + default-posture);
019_oral_history_testimony_consent and 021_testimony_separation_probe (the just-shipped L.1
governed-testimony machinery to reuse); the L.1 specification
(OBSERVATIONS_2026_06_19_PHASE_11_L1_SPECIFICATION.md); the DoR v2.1 W.1 entry (line 111) and W.6
entry (line 126). No caption/marginalia feature prior art exists in either repo (confirmed by grep;
the substring hits are incidental).

---

## Decisions (D-W1I2-1..6, ratified as recommended; founder sole adjudicator)

**D-W1I2-1 FACT-CLASS REUSE - RATIFIED (a).** Inc 2 REUSES the L.1 governed-testimony machinery
(append-only record table, non-strippable provenance stamp, member-only INSERT RLS,
GRANT-precedes-capture, separation probe + governance gate) rather than inventing a new foundation
(Reset Memo 8.2, No-New-Foundations). RECORDED SUPERSESSION: DoR v2.1 line 111 calls member captions
"the first arrival of the governed-testimony fact class." Git shows L.1 shipped that class first this
same day (migrations 019/020/021, frontend 73833bc). The DoR "first arrival" attribution is therefore
SUPERSEDED by L.1; captions are the SECOND arrival and a REUSE of the L.1 pattern, not the originating
instance. No DoR patch required this session (recorded as a reuse-divergence, the L.1-spec precedent
for the 010 consent supersession).

**D-W1I2-2 MINIMAL SLICE - RATIFIED (a) captions-only.** The first increment ships member CAPTIONS
only: a single-author remembered statement attached to one media item. MARGINALIA (communal
multi-author annotation, including the "may a member annotate another member's item" question and
all reaction/engagement boundaries) DEFERS to a successor increment, exactly as L.1 spun out its
display successor. Rationale: a caption is single-author-on-an-item, structurally isomorphic to L.1
testimony; marginalia is a different complexity and consent surface. The constitutional payload
(two-layer separation against the media provenance FACT layer, D-W1I2-4) is fully exercised by
captions alone. Deferred-not-foreclosed; becomes the marginalia successor increment.

**D-W1I2-3 CONSENT DIMENSION - RATIFIED (b) new dedicated category.** Captions bind through a NEW
dedicated W.6 consent category media_caption in member_consent_events, NOT the existing
attributed_quotes. Rationale (the 019 revocation-granularity argument, verbatim-applicable): revoking
attributed_quotes to withdraw one A/V Room caption would also withdraw every attributed quote
elsewhere in the vault (recaps, the future press-conference class). A member must revoke a caption
without collapsing all quote attribution. The DoR line 126 "W.1 attribution-level captions" wording is
descriptive and predates both the settled W.6 category model and the L.1 precedent; it does not bind
the category name. media_caption carries NO rendering_class (the existing class-iff-synth biconditional
holds unchanged). FOUNDER-APPLIED CHECK-widen (Charter section 7), same class as 010/017/019: the
EXECUTE agent prepares and verifies, the founder applies via the Supabase SQL editor; widening the
CHECK touches no existing row and adds no data.

**D-W1I2-4 SEPARATION PAYLOAD - RATIFIED (a) item-attach allowed, fact-layer walled.** THE PAYLOAD:
a remembered caption can never be read as, or merged into, a human-ratified provenance fact. The
W.1-specific sharp edge vs L.1: a caption legitimately MUST reference media_entries (the structural
meaning of "caption ON this item"), whereas L.1 testimony references nothing in the fact layer. The
ruling distinguishes three layers:
  - media_entries = the ITEM / corpus layer ("a photo exists"). A caption FK to it is the ALLOWED,
    necessary attach point.
  - media_provenance_tag_events = the human-ratified FACT layer (contributor/date/season/event/
    member_identification; ratified_by NOT NULL). The caption table has NO FK, NO trigger, NO write
    path here. WALLED.
  - the broader event ledger (artifacts, artifact_versions, approval_events,
    franchise_season_records, trophy_room_entries) - also WALLED.
Enforced STRUCTURALLY by a new SECURITY DEFINER caption_separation_probe() (booleans only,
fails-closed, inverse-of-G11) and a new governance gate G24 - the L.1 testimony_separation_probe()/G23
pattern re-pointed at the media FACT layer (the forbidden-confrelid set GAINS
media_provenance_tag_events, and conrelid targets media_captions). Specified in full in the increment
spec, section 5.

**D-W1I2-5 AUTHORSHIP SCOPE - RATIFIED (a) any member.** Any league member may caption any item (a
caption is "what I remember about this item," and any member may remember any item). Member-only
INSERT (author_user_id = auth.uid(); no commissioner proxy, W.6 1.3); append-only; attributed;
revocable-forward. Multiple members may caption the same item, each its own append-only row.
Contributor-only (b) was rejected: it would conflate the FACT-layer "who contributed the media" role
with the act of remembering.

**D-W1I2-6 DISPLAY RENDERING - RATIFIED (a) capture + display.** Unlike L.1 (which deferred display
because its consuming surface did not exist), the A/V Room EXISTS, so Inc 2 is CAPTURE + DISPLAY, and
is where the two-layer RENDERING invariant deferred from L.1 first gets BUILT. Captions render in the
existing A/V Room item view in a visibly-distinct "as remembered by [member]" panel, structurally
separate from the human-ratified provenance panel - never merged, no synthesized consensus; a caption
can never be styled or placed so as to read as a provenance tag. Capture-only (b) was rejected: the
consuming surface already exists and the DoR scopes captions as a displayed reveling act.

## Consent-dimension disposition (explicit output 2)

- **Category:** NEW media_caption in member_consent_events (D-W1I2-3).
- **Mechanism:** founder-applied CHECK-widen via the Supabase SQL editor (Charter section 7); EXECUTE
  prepares + verifies, never self-applies.
- **Bind:** GRANT-precedes-capture - no caption stored without a prior media_caption GRANT; absence =
  no grant (W.6 default-posture 1.4). ROUTE-enforced (the L.1 precedent: RLS gates ownership +
  append-only, the route gates the grant).
- **Revocation:** revocable-forward - a REVOKE withholds FUTURE display of the member's captions,
  never rewrites a captured row.
- **Read:** because display IS in scope (unlike L.1), league read at DISPLAY is gated by current
  media_caption GRANT + not-withdrawn (D-W1I2-6), not withheld at capture. The member_consent_current
  view picks media_caption up for free; no view change.

## Reconciliations recorded
- DoR "first arrival of the governed-testimony fact class" (line 111) SUPERSEDED by L.1 (D-W1I2-1).
- DoR "attribution-level captions" (line 126) does NOT bind the consent category; media_caption
  elected (D-W1I2-3).
- media_display_withdrawals (011, nullable media_entry_id minted for Inc 2) is REUSED for caption
  display-withdrawal; the spec adds the caption-targeting path, no new withdrawal class
  (No-New-Foundations).

## Boundaries (inherited, non-negotiable)
Facts append-only; narratives derived never fact-creating; AI assists humans approve; silence over
speculation; no analytics / optimization / engagement loops / prediction; architecture frozen.
Captions NEVER contaminate media_provenance_tag_events or the event ledger. Provenance tags stay
human-ratified, never AI-guessed. NO reaction counts, NO engagement metrics on captions, ever.

## Output / next
Increment spec brief filed same session
(OBSERVATIONS_2026_06_19_PHASE_11_W1_INC2_SPECIFICATION.md). STANDING: a FRESH prod object-existence
probe precedes any 022 apply (EXECUTE) - the repo-Done != prod-applied hazard. Docket:
W.1 Inc 2 -> IN-FLIGHT. FRONTEND build (the A/V Room and the testimony machinery are frontend; engine
has neither).

**State at ruling:** engine 8a90e62 / frontend 73833bc (both VERIFIED main); prod six-true at 021.
