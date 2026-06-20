# OBSERVATIONS 2026-06-19 - Phase 11 W.1 Increment 2 SPECIFICATION (member captions, A/V Room)

**Session type:** SPECIFICATION (increment chain: scope ruling + spec, per the W.1-admitted lighter
path). Authored to the per-surface constitutional memo template v1
(docs/templates/per_surface_constitutional_memo_template_v1.md). Engine doc-only; SKIPS prove_ci.
Append-only; supersedes nothing.

**Anchors VERIFIED this session (git, not brief):** engine 8a90e62 / frontend 73833bc, both main-only;
prod parity six-true at 021 (see scope ruling). **Ratified input (do not re-litigate):**
D-W1I2-1..6 (ruling memo OBSERVATIONS_2026_06_19_W1_INC2_SCOPE_RULING.md). Mode B: no shipped caption
operational state at HEAD (git ls-files confirms no media_captions / caption code).

---

## 1. Section 9.2 election
The increment ships CAPTURE + DISPLAY (D-W1I2-6), captions-only (D-W1I2-2). The deferred alternatives
(marginalia; a capture-only-then-display split) are named, not foreclosed. Confidence: HIGH (the
A/V Room consuming surface already exists, so display is exercised here, not deferred as in L.1).

## 2. Section-content verification block
SOURCE-VERIFIED this session: 011 substrate, 010 consent log, 019/021 L.1 machinery (all read
directly). CARRY-FORWARD for Reset Memo doctrine via the L.1 spec section 4 trace.

| Doctrinal substance | Source | Verdict |
|---|---|---|
| 2.3 five core principles | DoR v2.1; L.1 spec 4.1 | CONFIRM |
| 8.2 No-New-Foundations | this session: reuses L.1 pattern + 011 substrate + reuses media_display_withdrawals | CONFIRM |
| W.6 consent binds via event log | 010 + 019 read this session | SOURCE-VERIFIED |
| media_provenance_tag_events = human-ratified FACT layer | 011 read this session (ratified_by NOT NULL) | SOURCE-VERIFIED |

Load-bearing finding: media_display_withdrawals.media_entry_id was minted NULLABLE in 011
specifically "so Increment 2 can target a testimony id instead." Inc 2 reuses this class for caption
display-withdrawal; no new withdrawal table.

## 3. Identity and scope
### 3.1 What Inc 2 IS
A consented, attributed, append-only member CAPTION on an A/V Room media item - a remembered account
ABOUT an item - captured and DISPLAYED beside (and visibly distinct from) the human-ratified
provenance facts.
### 3.2 What Inc 2 is NOT
- NOT the provenance FACT layer. A caption NEVER contaminates media_provenance_tag_events (the
  payload, section 6.2).
- NOT marginalia (communal multi-author annotation) - that defers (D-W1I2-2).
- NOT a reaction/engagement surface - no counts, no metrics, ever (D-W1I2-6 boundary).
- NOT AI-authored - the member writes; the engine never guesses a caption (provenance tags likewise
  stay human-ratified).
### 3.3 Channel and scope
Text caption, member-identity-keyed (author_user_id = the PERSON via auth.uid()). One member
captioning one item end-to-end is the admissibility floor.

## 4. Doctrinal compliance (trace)
- Facts append-only: captions persist to an append-only table (no UPDATE/DELETE policy; the
  010/020 idiom). A correction is a new row.
- Narratives derived, never fact-creating: a caption is a member's words, never synthesized into
  consensus; accounts stored attributed and unmerged (section 6.3).
- AI assists, humans approve: the member authors and consents; display renders only granted,
  not-withdrawn captions.
- Silence over speculation: no caption without a grant; no grant is fabricated; an item with no
  caption simply shows none.
- No analytics / optimization / engagement / prediction: no metric on captions (section 6.6).
Confidence: HIGH.

## 5. Operational shape (Mode B - specified; FRONTEND build)
The A/V Room, the consent machinery, and the display route are frontend; the engine has none. This
section is what the EXECUTE build produces and is measured against.

### 5.1 Consent (D-W1I2-3) - migration 022a (founder-applied CHECK-widen, section 7)
Widen member_consent_events.category CHECK to add 'media_caption' (the 019 idiom). No
rendering_class; the class-iff-synth biconditional holds unchanged. Member-only INSERT already holds.
FOUNDER applies via the Supabase SQL editor; EXECUTE prepares + verifies, never self-applies.

### 5.2 The caption table - migration 022b (append-only)
media_captions:
  - id            uuid PK default gen_random_uuid()
  - media_entry_id uuid REFERENCES media_entries(id) NOT NULL   (THE ALLOWED ITEM ATTACH POINT)
  - author_user_id uuid REFERENCES auth.users(id)   NOT NULL    (the PERSON; member-only)
  - body          text NOT NULL
  - provenance    text NOT NULL DEFAULT 'MEMBER_CAPTION'
                  CHECK (provenance = 'MEMBER_CAPTION')          (non-strippable S1 stamp, value-pinned)
  - recorded_at   timestamptz NOT NULL DEFAULT now()
  - supersedes    uuid REFERENCES media_captions(id)             (a correction is a new superseding row)
NO FK to media_provenance_tag_events, NO FK to any event-ledger table, NO trigger. Index on
(media_entry_id, recorded_at DESC). league scoping is derived through the parent media_entries row
(the media_provenance_tag_events precedent), so no separate league_id column is required for RLS.

### 5.3 RLS (the 011 + L.1 posture)
- SELECT: league-authenticated (members + commissioner browse captions in the room), scoped through
  the parent media_entries row - the media_provenance_tag_events_select precedent. The
  consent/withdrawal DISPLAY gate lives in the route (5.6), matching 011's "gate-reading happens in
  the display route."
- INSERT: member-only (author_user_id = auth.uid()). Deliberately NO is_commissioner/is_admin -
  the commissioner cannot proxy a caption (W.6 1.3). The route enforces the media_caption GRANT
  before INSERT (GRANT-precedes-capture; RLS enforces ownership + append-only, the route enforces
  the grant - the L.1 route-enforced precedent).
- NO UPDATE policy, NO DELETE policy: append-only via default-deny.
Considered, not elected: author+admin-only SELECT (the strict L.1 capture posture). Rejected because
captions are a DISPLAYED reveling act (D-W1I2-6); protection is the GRANT-gated display +
revocable-forward + withdrawal, not capture-time read denial. Founder may tighten at the
revision-point if room-read proves too open.

### 5.4 Display-withdrawal reuse (No-New-Foundations)
Caption display-withdrawal rides the EXISTING media_display_withdrawals (011), whose media_entry_id is
nullable by design for Inc 2. The build adds a caption-targeting column path: either a nullable
caption_id REFERENCES media_captions(id) added by 022b, or the existing nullable media_entry_id reused
to carry the caption's parent item with a target discriminator. EXECUTE picks the minimal shape that
keeps the table append-only and the display route's "honor latest withdrawal" semantics intact;
records the choice. No new withdrawal class.

### 5.5 Separation probe + gate (D-W1I2-4) - migration 022c
caption_separation_probe() SECURITY DEFINER, booleans only (no caption content), STABLE,
search_path = public, pg_catalog. Asserts:
  (i)   media_captions exists;
  (ii)  media_captions.provenance is present AND NOT NULL (the non-strippable stamp);
  (iii) NO foreign key from media_captions references media_provenance_tag_events OR any event-ledger
        table (artifacts, artifact_versions, approval_events, franchise_season_records,
        trophy_room_entries) - i.e. the ONLY permitted confrelid is media_entries (the item attach
        point); any FK into the FACT layer or ledger fails the probe;
  (iv)  NO user-defined (non-internal) trigger fires on media_captions;
  (v)   a MISSING object -> existence boolean FALSE, so the gate fails closed (inverse-of-G11).
This is the 021 testimony_separation_probe re-pointed: conrelid = media_captions; the forbidden
confrelid set GAINS media_provenance_tag_events; media_entries is explicitly the allowed attach point.
New gate G24 in scripts/test-governance.ts calls the probe via serviceClient.rpc and FAILS when any
boolean is false (the G23 pattern).

### 5.6 Capture + display surface
- Capture: a member-authored caption box on the A/V Room item view; the route checks the current
  media_caption GRANT (member_consent_current) BEFORE INSERT; absence = no capture (fail-closed).
- Display: the item view renders TWO visibly-distinct layers - the human-ratified PROVENANCE panel
  (verified: contributor/date/season/event, derived latest-non-withdrawn over
  media_provenance_tag_events) and, structurally separate, the "as remembered by [member]" CAPTIONS
  panel (each caption attributed, gated by current media_caption GRANT AND not-withdrawn). The two
  panels are never merged; no consensus is synthesized; a caption is never styled or placed so as to
  read as a provenance tag (the two-layer rendering invariant, built here for the first time).

### 5.7 Lifecycle
GRANT (member_consent_events, media_caption) -> media_captions INSERT (route-gated on the grant) ->
caption renders in the room IFF grant current AND not withdrawn. REVOKE withholds future display;
never edits a row. A correction is a new superseding caption row.

## 6. Surface-specific invariants
- 6.1 Append-only at every surface (no UPDATE/DELETE; a correction is a new row).
- 6.2 THE PAYLOAD: a caption provably cannot be read as / merged into a human-ratified provenance
  fact - enforced STRUCTURALLY by 5.5 (no write path to media_provenance_tag_events or the ledger;
  fails-closed probe), not by prompt guardrail.
- 6.3 No synthesized consensus: captions stored attributed and unmerged; two members' captions on one
  item are preserved as two accounts, never reconciled.
- 6.4 GRANT precedes capture (media_caption; absence = no grant).
- 6.5 Member-only authorship (author_user_id = auth.uid(); no commissioner proxy).
- 6.6 Captions are league memory, not engagement data: no counts, no metrics, ever.
- 6.7 Specification governs the live baseline; divergence is a revision-point event, not a quiet drift.

## 7. Governance
| Decision | Authority | Mechanism |
|---|---|---|
| Author / consent to a caption | MEMBER only | member_consent_events media_caption GRANT + member-only INSERT |
| Read captions in the room | league-authenticated | RLS SELECT through parent media_entries; DISPLAY gated by grant + withdrawal in the route |
| Withdraw a caption from display | commissioner (honor) / member (request) | media_display_withdrawals (reused), append-only |
| Revoke (forward) | MEMBER only | member_consent_events REVOKE (revocable-forward) |
| Add the media_caption category | FOUNDER applies | CHECK-widen via Supabase SQL editor (section 7 escalation) |
| Spec amendment at revision-point | founder | section 8 |
| Promotion _observations -> docs | founder | after one caption end-to-end + G24 green |

## 8. Revision-point
### 8.1 Anchor: the earlier of (a) one member's caption captured AND displayed end-to-end, or
(b) the post-Tahoe review. ### 8.2 Evaluates: did capture + the two-layer display work; did the
separation invariant hold (G24 green; caption_separation_probe all-true on prod); consent-flow fit
(GRANT-precedes-capture friction); whether to build the marginalia successor next; whether
league-read (5.3) proved too open. ### 8.3 One full cycle = one caption authored under grant,
rendered in the distinct panel, and revocable-forward proven (REVOKE withholds display).
### 8.6 Triggered revision (anchor-independent): ANY finding that a write path from media_captions to
media_provenance_tag_events or the event ledger exists triggers immediate revision.

## 9. Cluster / sequencing carry-forward
### 9.1 W-cluster: the MARGINALIA successor increment carries forward (communal multi-author
annotation; the "annotate others' items" question; still no reaction counts / engagement). ### 9.2
W.8 Memorabilia Pipeline stays REGISTER-only (rides L.1 + W.4; no build authority conferred). ### 9.3
Docket: behind W.1 Inc 2 - W.2 art direction / W.3 corkboard / W.5 trophy taxonomy (overflow per the
July-to-August DoR plan). ### 9.4 Roadmap admissible set adds: the marginalia successor.

## 10. Prior-attempt findings
No failed prior attempts; the increment chain proceeds cleanly. The L.1 chain (019/020/021) is REUSE
art, not a failed attempt. Confidence: HIGH on absence-of-findings.

## 11. Adaptations from template v1
- Chain compression: an admitted-surface INCREMENT, so selection-prep + decision-readiness collapse
  into the scope ruling; section 1 records the ruling's election.
- Surface-specific divergence vs L.1: a caption legitimately FKs the ITEM layer (media_entries) while
  the FACT layer (media_provenance_tag_events) is walled - the separation probe (5.5) distinguishes
  allowed-item-attach from forbidden-fact-write, a sharper claim than L.1's zero-ledger-FK.
- Display IS in scope (vs L.1 capture-only): the two-layer RENDERING invariant deferred from L.1 is
  built here (5.6).
- Single append-only table (a caption is one row), not L.1's two-table session/exchange split.
Confidence: HIGH.

## 12. Confidence labeling
### 12.1 Highest: the two-layer separation is the payload and is STRUCTURALLY provable (5.5 / 6.2);
media_display_withdrawals reuse (No-New-Foundations); media_caption dedicated category (revocation
granularity, 019 precedent). ### 12.2 Medium-high: league-authenticated SELECT with route-gated
display (strict author+admin SELECT named, not elected). ### 12.3 Medium: the exact withdrawal-target
shape in 5.4 (EXECUTE records the minimal choice). ### 12.4 Deliberate silences: marginalia semantics
(successor); any promotion of a caption into the provenance FACT layer (never automatic; out of scope).

---

**State at specification:** engine 8a90e62 / frontend 73833bc (both VERIFIED main); prod six-true at
021. W.1 Inc 2 SPECIFIED. First EXECUTE unit (frontend): 022a media_caption CHECK-widen
(founder-applied) -> 022b media_captions append-only table + display-withdrawal target path ->
022c caption_separation_probe() + G24 gate -> capture + two-layer display surface in the A/V Room.
STANDING: a FRESH prod object-existence probe on qcaxemuydxlzpzgnnnoa precedes any 022 apply
(EXECUTE). Doc-only; _observations placement; SKIP prove_ci; one topic.
