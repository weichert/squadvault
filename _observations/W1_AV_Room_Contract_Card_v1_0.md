# W.1 Mr. Herlth's A/V Room - Contract Card v1.0
## Four-memo chain, memo 3 of 4

**Surface ID:** W1_AV_ROOM
**Status:** RATIFIED 2026-06-10 (chain D-W1-1..6 as recommended); filed provisional in
`_observations/` with the chain; promotes alongside the spec (recommended destination
`docs/30_contract_cards/clubhouse/`, founder elects at promotion).
**Verified anchors:** engine `1782e3b` - frontend `248895c`.
**Precedent shape:** Rivalry Chronicle v1 Contract Card; extended with the W.6 section 7.2
consent declaration, which is a mandatory contract-card field for any surface touching
member likeness, voice, or attributed words.

## Purpose

Preserve and present the league's archival photo/video corpus with human-ratified
provenance, room-level consent, and - post-E2.3 - member captions and marginalia as
governed testimony, under append-only discipline, with all member-identifying display,
voice playback, and attributed words gated on current per-member consent.

## Fact classes carried (system of record: frontend Supabase, D-W1-6)

| Class | Authored by | Ratified by | Append-only mechanism |
|---|---|---|---|
| Media archive entry | Commissioner (upload) | The upload act (C3 attribution) | RLS default-deny, SELECT+INSERT only |
| Provenance tag event (contributor / date / season / event / member_identification) | Commissioner; member self-identification in Increment 2 | The tag-ratification act; corrections supersede | same |
| Room ratification event | Commissioner | The ratification act; display fail-closed without it | same |
| Media testimony (caption / marginalium) | The member, only (`auth.uid()` enforced) | The member's authenticated, 2d-consented act | same |
| Display withdrawal | Member requests | Commissioner ratifies | same |

None of these classes enters the engine's canonical event ledger, ever.

## Required inputs (authoritative)

- The original media file (the retained source - stored unmodified)
- Authenticated commissioner identity for ingest/tagging/room acts
- Authenticated member identity for testimony and self-identification (Increment 2)
- `member_consent_current` derived state (frontend migration 010) for every consent gate

## Derived inputs (allowed)

- Current tag state per (entry, kind): latest non-withdrawn tag event
- Current consent state per (member, category): the 010 view
- Thumbnails/renditions regenerated from the original

No AI-derived inputs of any kind. No rankings, trends, view data, or activity data exist.

## W.6 section 7.2 consent declaration (BINDING)

Per the ratified W.6 memo, this surface declares: (a) the categories it READS, (b) at
which of the three gates, and (c) behavior on revocation. Absence of a current grant in
`member_consent_current` = ungranted = no use (default-posture law, W.6 1.4). All gates
fail closed.

| Category read | Capture gate | Derivation gate | Publication gate | On revocation (W.6 section 4, D-U(b) artifact-integrity) |
|---|---|---|---|---|
| 2a `media_appearance` | not read (raw corpus capture is governed by room-level ratification, not 2a - W.6 section 2 boundary clause; identification, not existence, is 2a's subject) | READ: ratifying a `member_identification` tag is the identifying derivation; tag UI shows grant state read-only | READ: identified display (name shown, member-focused filtering) renders only against a current grant | identified display stops forward; tag events remain in the record; no new identification-derivations; display withdrawal additionally available |
| 2b `recorded_voice` | not read (archival items were recorded in the past; W.1 captures no new voice) | not read in v1 (no generator consumes audio) | READ: playback of video audio containing a member's voice requires that member's current grant; commissioner-attested no-member-voice items exempt; fail closed | playback of affected items stops forward; the files remain preserved in the corpus, untouched |
| 2d `attributed_quotes` | READ: caption/marginalium submission requires the author's current grant at the write path | not read in v1 (no generator consumes testimony; any future consumer - W.4, W.8, L.2 - declares its own derivation read in its own chain, via W.6 7.3 allowlists) | READ: render reads current state; revoked testimony stops rendering forward | no new capture; no new display derivation; artifacts already approved and published elsewhere remain sealed intact per D-U(b); display withdrawal additionally available |

Categories NOT read: 2c `likeness_derived` (no derived/rendered artifacts are produced by
this surface; W.8/W.4 own that gate) and 2e `synthesized_voice` (nothing is synthesized,
ever, on this surface).

Layering (W.6 D-W): room-level ratification (the corpus exists and is shared) ->
member-level W.6 grant -> item-level ratified tag/caption that reads the grant. Room-scope
grants nothing per-member. The commissioner sees per-member grant state read-only at the
gates and never sees aggregate consent statistics (W.6 1.5).

## Output structure (the room's render contract)

- Corpus browse: photo-first; chronological/era ordering only (no algorithmic ordering)
- Per-item view: the media itself; the provenance panel (ratified tags, with honest gaps
  rendered as gaps); the testimony layer (Increment 2), visibly distinct and labeled as
  the member's words
- Undated/untagged items display honestly undated/untagged - never interpolated
- Empty states render empty; the room fails closed without a room ratification event

## Invariants

- Fact immutability and append-only discipline on every class
- Human ratification on every provenance claim; no AI assertion path exists
- Consent gates fail closed against derived current state
- Testimony visibly distinct from verified record, always
- Member behavior never measured; no telemetry, no engagement mechanics, no prompting
- Silence is valid and preferred: empty over guessed, silent over inferred
- The original file is never modified; corrections and withdrawals are new events

## Failure modes

- No room ratification event -> room renders nothing (fail closed, explicit)
- Missing/partial provenance -> displayed as honest gaps
- Absent or revoked 2a -> identification silent; item still displays un-identified
- Absent or revoked 2b -> video playback disabled for that item; file preserved
- Absent or revoked 2d -> caption write rejected at capture / render stops forward
- Storage object missing for an entry -> entry shows an explicit unavailable state;
  never silently dropped
- Any attempted UPDATE/DELETE on a record class -> denied by RLS default-deny

## Approval

- Every ingest, tag ratification, room ratification, and withdrawal ratification is an
  explicit authenticated human act, attributed in the row
- Every testimony row is the member's own authenticated, consented act
- The chain (memos 1-4) binds only on explicit founder ratification of D-W1-1..6
