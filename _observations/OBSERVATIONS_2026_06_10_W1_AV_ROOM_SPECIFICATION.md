# OBSERVATIONS 2026-06-10 - W.1 Mr. Herlth's A/V Room: Specification
## Four-memo chain, memo 2 of 4 - per-surface constitutional memo per template v1.0

**Date:** 2026-06-10
**Session:** Fable DECIDE (Charter v1.0 section 2.1).
**Status:** RATIFIED 2026-06-10 (D-W1-1..6 as recommended; chain memo 1). Authored against
template v1.0 (`docs/templates/`), Mode B (specified-shape). Opus builds against this
document; acceptance criteria derive from sections 5 and 6. Increment 1 is the v1 build;
Increment 2 is specified, build gated on E2.3.
**Verified anchors:** engine `1782e3b` - frontend `248895c`.
**Chain siblings:** constitutional admission memo (memo 1, the gate adjudications and
decision register); contract card (memo 3, the binding consent declaration); admission
record (memo 4, registration).

---

## 1. Section 9.2 election

The framing question the predecessor chain surfaced: **does v1 ship the foundation half
now and defer member testimony to E2.3, or wait and ship whole?** This is D-W1-1. The
founder's pre-chain leaning (recorded at engine `1782e3b`) is option (a): ship
founder/commissioner ingest + ratified provenance + room consent + display now; fully
specify the governed-testimony class now; gate the member-facing build on E2.3. This
spec is authored against election (a) throughout - Increment 1 is the v1 build,
Increment 2 is specified-but-gated. If the founder ratifies (b) instead, sections 5.6-5.7
move from gated to v1 scope and nothing else in this spec changes - the specification was
deliberately written so the election swings build sequencing, not design.

Confidence on the election: high that (a) is the operative reading (founder-stated,
hash-anchored); the formal pick still occurs at ratification.

## 2. Section-content verification block

**Methodology: fresh source reads, this session.** No carry-forward was needed - the
chat-session environment had repo access. Read fresh: Charter v1.0; STATE.md (both the
engine ledger and the kickoff brief it points to); DoR v2.1 in-repo (Part 3 W.1 + standing
law, Part 6 D-G, Part 8, v2.1.1 supersession note); W.6 memo v1.2 (ratified) including
Appendix A; the Manual Fact Import frame; SAT v1; template v1.0; frontend migrations
001/003/010 and the `src/app/league/[id]` tree; engine commits `93c2f3a`/`1782e3b`.

Drift findings and dispositions:
- **Four-memo naming gloss** (brief vs template section 3.10): reconciled in chain memo 1
  section 3.1; disposition = recorded, no patch needed.
- **Brief's expected consent declaration incomplete** (omitted 2b, which W.6 section 2
  binds to "W.1 video audio"): disposition = chain adds 2b; consequence adjudicated in
  D-W1-1; flagged to founder in the close-out.
- **No other brief claim failed verification.** All anchors matched git.

## 3. Identity and scope

### 3.1 What the surface is

Mr. Herlth's A/V Room is the league's archival media room: the permanent, login-gated home
of the photo and video corpus, each item carried as an append-only media entry with
human-ratified provenance (who contributed it, when it was taken, which season, what
occasion), shared with the league by the commissioner's room-level ratification, and -
once members exist as authenticated identities with consent grants - annotated by the
members themselves with captions and marginalia that are governed testimony: attributed,
consented, append-only, and visibly distinct from every verified fact. It is a Permanence
surface (the corpus outlives platforms and members) that becomes a Voice surface the day
the first member caption lands.

### 3.2 What the surface is not

- Not the substrate and not the event ledger: nothing in the room asserts a score, a
  transaction, or any verified event; media facts and testimony never enter the engine's
  canonical ledger (D-W1-6).
- Not the Trophy Room, the Member Office, the corkboard (W.3), or the memorabilia
  pipeline (W.8) - W.8 will later read this corpus to propose set dressing; that is W.8's
  chain.
- Not a feed and not a social network: no infinite scroll, no algorithmic ordering, no
  reactions, no counters, no unread badges, no notifications.
- Not a watch party: no synchronous mechanics in v1 (DoR verbatim boundary).
- Not an AI tagging tool: no proposal path of any kind exists in v1; every provenance
  claim is human-entered and human-ratified.
- Not a public gallery: no unauthenticated render path; no public bucket.

### 3.3 Content classes (native admission set)

| # | Class | Kind | v1 build |
|---|---|---|---|
| 1 | Media archive entry (photo or video + its display) | append-only record + stored original | Increment 1 |
| 2 | Provenance tag event (5 kinds per D-W1-3) | append-only ratification event | Increment 1 |
| 3 | Room ratification event | append-only governance event | Increment 1 |
| 4 | Media testimony (caption / marginalium) | governed-testimony fact (2d) | Increment 2, gated on E2.3 |

Classes 1-3 are display/governance records; class 4 is the first arrival of the
governed-testimony fact class formalized in chain memo 1 section 4.

### 3.4 Temporal scope

The whole league history - the existing corpus spans the ~40-year league and the 16-season
digital era. Date provenance uses honest partial precision (D-W1-3); items with unknown
dates display undated, in an explicitly undated shelf position, never interpolated.

### 3.5 The two increments (the D-W1-1 shape)

- **Increment 1 (v1 build):** bucket + media entries + provenance tagging + room
  ratification + commissioner upload/tagging surface + the A/V Room display route.
  Buildable entirely against the commissioner's identity. Video items store and preserve;
  playback of items containing member voices is inert pending 2b grants (videos
  commissioner-attested as containing no member voice may play); photos display fully.
- **Increment 2 (specified now, build gated on E2.3):** member captions, member
  self-identification tagging, marginalia - the member-testimony features. Their schema,
  gates, and rendering are specified in this document so that E2.3's completion unblocks a
  pure execution brief with zero further adjudication.

## 4. Doctrinal compliance trace

- **4.1 Constitution / Reset Memo section 2.3 five principles.** Facts immutable and
  append-only: every class in 3.3 is append-only under the F4 sibling discipline; an edit
  is a superseding event. Narratives derived, never fact-creating: the room renders
  records; it generates no prose. AI assists, humans approve: stronger here - v1 has no AI
  involvement at all; every act is a human's. Silence over speculation: empty axes stay
  empty; absent grants mean no display; an empty room renders empty. No analytics /
  optimization / engagement loops / prediction: section 6 invariants 6.3-6.5.
- **4.2 Reset Memo section 4.4 (social surface vs social network).** Marginalia are
  asynchronous communal presence on shared history - a guest book on the wall, not a
  network: no graph, no follows, no reactions, no virality mechanics, chronological and
  finite.
- **4.3 Reset Memo section 8.2 (No-New-Foundations) and provisional filing.** Supabase
  Storage is a new foundation - and the DoR Part 3 W.1 mandate names it verbatim, so the
  foundation is DoR-authorized and enters via this chain, not by accretion. The spec files
  provisional in `_observations/` per Phase 11 precedent; promotion per section 8.4.
- **4.4 Reset Memo section 8.4 (closure certifications).** W.1 is Track W, not a Phase 11
  closure surface; its evidence contributes to cert 4 (shipping pattern) and cert 5
  (framing) at most. No closure dependency is created.
- **4.5 Section 9.2 (artisan frame).** The room is built for PFL Buddies' actual corpus,
  ingested by the founder's hands, exquisite for ten people. Generalization is carried by
  the class design (testimony, provenance, room ratification are domain-agnostic), not by
  speculative configurability.
- **4.6 Track W/L standing law (DoR Part 3 line 109).** Member words can become facts -
  attributed, consented, append-only (class 4). Member behavior is never measured: no
  view counts, no dwell, no per-member activity surface, ever. No telemetry, no autonomous
  publication, no engagement loops.
- **4.7 W.6 bindings.** The contract card carries the mandatory 7.2 declaration (2a at
  derivation+publication; 2b at publication; 2d at capture+publication; revocation
  semantics per W.6 section 4 D-U(b)). Default-posture law honored structurally: gates
  read `member_consent_current`; absence = no use. Room-scope vs member-scope layering
  per D-W. Commissioner sees grant state read-only at the tag-ratification surface;
  never aggregate statistics (W.6 1.5).
- **4.8 DoR Part 8 prohibitions.** No member likeness in generated art (no generation
  exists here); no synthesis; no feeds/badges/notification pressure; no prediction. All
  structurally absent.

## 5. Operational shape - Mode B (specified shape)

Mode election: no W.1 operational state exists at HEAD (findings F1-F2); pure Mode B.
Binding shapes below; exact DDL, file names, and component structure are the Opus build's
work. Where a column list is given it is the binding minimum, not a frozen schema.

### 5.1 Storage (D-W1-2)

One private bucket `league-media`. Object path
`{league_id}/{media_entry_id}/original.{ext}`. No public policy; no client-direct
write - uploads pass through the authenticated commissioner surface (server-side). Reads
render via short-TTL signed URLs issued server-side within the login-gated
`/league/[id]` tree only. Derived renditions (thumbnails), if built, live under the same
entry prefix and are regenerable - the original is the retained source (C2) and is never
modified.

### 5.2 `media_entries` (append-only)

Minimum: `id` (uuid), `league_id`, `media_kind` (`photo` | `video`),
`storage_path`, `mime_type`, `uploaded_by` (auth identity - the C3 attribution),
`upload_note` (optional), `created_at`. RLS: SELECT for league-authenticated viewers;
INSERT commissioner-only; no UPDATE/DELETE policy (F4 discipline). Removal from display
is a display-withdrawal event (5.5), never a row deletion.

### 5.3 `media_provenance_tag_events` (append-only)

Minimum: `id`, `media_entry_id`, `tag_kind` (`contributor` | `date` | `season` | `event`
| `member_identification`), `tag_value` (kind-shaped; `date` carries value + precision:
`exact` | `year` | `season`), `tagged_member_user_id` (nullable; required iff
`member_identification`), `ratified_by`, `note`, `recorded_at`, `supersedes`
(nullable self-reference - a correction names what it supersedes). Current tag state per
(entry, kind) is a derived read: latest non-withdrawn event. RLS: SELECT league-wide;
INSERT commissioner-only in Increment 1 (Increment 2 adds member self-identification:
INSERT where `tagged_member_user_id = auth.uid()` and kind = `member_identification`);
no UPDATE/DELETE.

Display rule for `member_identification`: the identification renders (name shown,
member-focused filtering) only against a current 2a grant in `member_consent_current`;
otherwise the tag event exists but the display is silent. Never AI-guessed: there is no
write path that is not an authenticated human's act.

### 5.4 `room_ratification_events` (append-only)

Minimum: `id`, `league_id`, `ratified_by` (commissioner), `scope_note`, `recorded_at`.
One initial event ratifies the room is shared with the league (D-W1-4); the display route
renders nothing until it exists (fail-closed). Per-item ingest attribution is carried by
`media_entries.uploaded_by` - no per-batch ceremony.

### 5.5 Display withdrawal (sibling event class)

Per W.6 section 4: member-requested, commissioner-ratified, item-scoped withdrawal from
forward rendering; the record stands. Minimum: `id`, `media_entry_id` (or testimony id),
`requested_by`, `ratified_by`, `recorded_at`, `note`. Withdrawal is a courtesy mechanism,
never automatic, never deletion. (This is the same class shape W.6 D-V named as the
consent system's sibling; if the consent build's withdrawal table already exists at build
time, W.1 reuses it rather than minting a twin - the Opus session verifies at HEAD.)

### 5.6 `media_testimony` (Increment 2; append-only; the governed-testimony class)

Minimum: `id`, `media_entry_id`, `member_user_id` (author - `auth.uid()` enforced at
INSERT, the migration-010 discipline), `shape` (`caption` | `marginalium`), `body`
(verbatim, the C2 retained source), `recorded_at`. RLS: SELECT league-wide; INSERT
member-only with a current 2d grant verified at the write path (capture gate); no
UPDATE/DELETE. Publication gate: render reads current 2d state; revoked-after-capture
testimony stops rendering forward (D-U(b): no new derivation; the record stands; display
withdrawal additionally available). Rendering: visibly distinct layer from provenance
tags and from any verified fact - labeled as the member's words, never as the record.
Marginalia: chronological, finite, unthreaded; no reactions, counters, or badges.

### 5.7 Routes and surfaces

- `/league/[id]/av-room` - the room: corpus browse (photo-first), per-item view with
  provenance panel (ratified tags, honest gaps), testimony layer (Increment 2), shelf
  presentation deferred to W.2's aesthetic pass (the VHS-shelf detail is W.2's,
  zero schema impact - DoR W.2).
- `/league/[id]/av-room/ingest` (commissioner-only) - upload + tagging: photo-first
  tooling per D-G (drag-drop images, batch tagging; video accepted), tag entry across the
  five kinds, grant-state shown read-only beside member-identification tagging (W.6 5),
  superseding-correction flow.
- Video playback: enabled per item only when (no member voice attested by commissioner
  tag/note) or (all identified members' 2b grants current). Fail-closed.

### 5.8 What Increment 1 explicitly does not build

Member-facing writes of any kind; AI proposal of any kind; W.8 match surfacing; W.2
aesthetics beyond a plain, dignified default; corkboard announcements (W.3's);
engine-side anything.

## 6. Surface-specific invariants

- **6.1** Every W.1 record class is append-only under RLS default-deny (SELECT+INSERT
  only); corrections supersede; nothing mutates or deletes. (Constitution; F4.)
- **6.2** Provenance is human-ratified, never AI-asserted; no AI write or proposal path
  exists on this surface. (DoR W.1 verbatim.)
- **6.3** Member behavior is never measured: no view/play counts, no per-member activity
  data, no aggregate consent statistics, no telemetry. (Standing law; W.6 1.5.)
- **6.4** No engagement mechanics: no feed, no infinite scroll, no algorithmic ordering,
  no reactions, no counters, no badges, no notifications. (Part 8; Reset 4.4.)
- **6.5** No prediction, no prompting: the room never nudges members to caption, tag,
  grant, or visit. (Standing law; W.6 3 anti-re-prompt clause.)
- **6.6** Consent gates fail closed and read derived current state only; absence of a
  grant is no use. (W.6 1.4, 7.2; contract card binding.)
- **6.7** Testimony and verified facts render as visibly distinct layers, always.
  (W.6 consistency 3; chain memo 1 C1 analogue.)
- **6.8** Partial truth, never gap-filling: empty axes render empty; unknown dates are
  undated; nothing is interpolated. (C4 analogue.)
- **6.9** The original media file is the retained source: stored unmodified, never
  edited in place; renditions are derived and regenerable. (C2 analogue.)
- **6.10** Specification governs live baseline; the live baseline does not silently
  revise the specification. (Template universal invariant.)

## 7. Governance

| Decision | Authority | Mechanism |
|---|---|---|
| Media ingest (upload approval) | Commissioner | authenticated ingest surface; `uploaded_by` attribution |
| Provenance tag ratification / correction | Commissioner (member self-identification in Increment 2) | append-only tag events; superseding flow |
| Room-level ratification | Commissioner | `room_ratification_events`; display fail-closed without it |
| Consent grants (2a/2b/2d) | The member, only | W.6 system of record (`member_consent_events`); never proxied |
| Display withdrawal | Member requests; commissioner ratifies | withdrawal event class (5.5) |
| Increment 2 build authorization | Founder | E2.3 completion + execution brief per Charter 5 |
| Spec amendment at revision point | Founder | section 8 |
| Spec amendment between revision points | Founder | separate dated memo (supersession discipline) |
| Promotion `_observations/` -> `docs/` | Founder | section 8.4 |
| Map registration | Founder | docs-Map patch per registration-as-commissioning |

Members are not "users": they are the league. They are never analytics subjects, never
segmented, never prompted. Their words enter the record only by their own authenticated,
consented act.

## 8. Revision point

- **8.1 Primary anchor (event):** completion of E2.3 member onboarding for the first
  member cohort - the moment Increment 2 becomes buildable. The revision point evaluates:
  Increment 2's spec against onboarding reality; the 2b video-playback posture against
  actual grant states; tag-taxonomy fit against the founder's ingest experience.
- **8.2 Secondary checkpoint (calendar):** NFL Week 1 (~2026-09-08), for cross-surface
  consistency with the Phase 11 anchors - evaluates founder-ingest ergonomics and display
  reception even if E2.3 has not completed.
- **8.3 One full cycle semantics:** W.1 is browse-cadenced; "one full cycle" = one real
  ingest wave (a founder batch of genuine corpus media, tagged and displayed) plus, for
  Increment 2, one member's first caption landing through the full gate path.
- **8.4 Promotion criteria:** Increment 1 built and gates green; at least one real ingest
  wave displayed; founder election. Increment 2 need not be built for the spec to
  promote - the spec's Increment 2 sections promote as specification, with E2.3 as
  their recorded build gate.
- **8.5 Alternatives considered:** calendar-only anchor (rejected: the spec's open half
  is event-gated on E2.3, not on the season); draft-day anchor (rejected: that is L.3's
  clock; W.1 should not borrow it).
- **8.6 Triggered revision:** any operational finding that surfaces a spec gap (storage
  policy surprise, consent-read ergonomics, tag-taxonomy miss) may trigger revision
  between anchors by dated memo.

## 9. Track sequencing carry-forward

- **9.1 Track W after W.1:** W.2 (art direction) is the natural next per the master
  sequence and consumes this room as its richest canvas (shelf-of-VHS-tapes presentation
  lands there); W.3 corkboard independent; W.4 docket independent; W.5 chain independent
  (SAT exercise #2); W.8 gains its corpus precondition when Increment 1 ships and its
  testimony precondition at L.1.
- **9.2 Track L:** L.3's August clock is unblocked by W.6 (already) and is not behind
  W.1 structurally - but W.1 is sequenced first per the founder's calendar reasoning
  (`1782e3b`). L.4 will reuse this surface's storage + playback patterns and the 2b gate
  shape. L.1 inherits the governed-testimony formalization (chain memo 1 section 4)
  wholesale.
- **9.3 Track E:** E2.3 onboarding now has its destination surface ("members arrive to a
  furnished room"); the DoR's sequencing note (outreach coincides with W.1 going live)
  stands.

## 10. Prior-attempt findings

None. The chain proceeded cleanly from the kickoff brief; no prior failed W.1 attempt
exists in the record. Confidence: high (grep over `_observations/` and STATE.md shows no
prior W.1 chain artifacts).

## 11. Adaptations from template v1.0

1. **Chain composition:** a constitutional admission memo (chain memo 1) and a contract
   card (chain memo 3) accompany this spec, because W.1 trips the new-fact-class and
   consent gates that no Phase 11 A-cluster surface tripped, and W.6 7.2 makes the
   contract-card declaration mandatory. The spec itself remains template-conformant; the
   chain around it is wider. Candidate template-revision input if W.5/L.1 repeat the
   pattern (template section 5.2 two-instance rule).
2. **Section 8 anchor is an event (E2.3), not a calendar date** - first instance of an
   event-primary anchor; template section 3.8 admits it ("calendar-fixed moment,
   event-anchor, or hybrid").
3. **Section 9 repurposed from Phase 11 cluster carry-forward to Track W/L sequencing**
   - W.1 is the first non-Phase-11 surface to use the template; the section's purpose
   (what remains admissible, what sequences behind) transfers cleanly.
4. **Section 1's election was founder-pre-leaned in-repo** (`1782e3b`) rather than
   surfaced by a decision-readiness memo - a Track W pattern worth watching.

## 12. Confidence labeling

- **12.1 Highest:** the substrate findings and gate placements (independently verified);
  the append-only shapes (direct siblings of shipped migrations 001/010); the consent
  reads against `member_consent_current` (the view exists and its absence-semantics are
  documented in-migration).
- **12.2 Medium-high:** the storage path/access model (standard Supabase posture; founder
  may amend TTL/path conventions without spec damage); the five-kind tag taxonomy
  (founder ratifies at D-W1-3); the withdrawal-class reuse note in 5.5 (verify at build
  HEAD).
- **12.3 Medium:** the 8.3 cycle semantics (first browse-cadenced Track W surface; thin
  precedent); video playback ergonomics under the 2b posture (constitutionally forced,
  product-judged).
- **12.4 Deliberate silences:** no DDL, no component code, no aesthetic direction (W.2's),
  no W.8 mechanics, no AI proposal design (none exists to design), no engine plumbing
  (no consumer exists). Silence over speculation.
