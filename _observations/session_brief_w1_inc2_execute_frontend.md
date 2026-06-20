# Session brief - W.1 Inc 2 EXECUTE (member captions: capture + two-layer display) - FRONTEND build

ROLE and ROUTING. EXECUTE session (Claude Code, Opus), FRONTEND repo. This builds the unit
GREEN-LIT by the W.1 Inc 2 specification (engine 905cb1c). It is an IMPLEMENTATION session: the
architecture is ratified, do not re-litigate D-W1I2-1..6. Use native Write + git + gh (NOT the legacy
heredoc / pathlib.write_text / glob-without-.md idioms - those are DECIDE-chat paste workarounds,
obsolete here per CLAUDE.md). Distrust this brief; git wins over every claim in it.

ANCHORS AT AUTHORING (2026-06-19 - VERIFY, do not trust):
- Engine main = 905cb1c (the spec + scope ruling live here; doc-only, you READ from it, you do not
  build here).
- Frontend main = 73833bc (this is where you build).
- Both main-only. Frontend migrations stop at 021; 022 is the next free number. test-governance.ts
  G23 is the last gate (G24 is yours). Prod qcaxemuydxlzpzgnnnoa was six-true at 021 when the spec was
  filed - RE-PROBE before applying anything (the standing precondition; repo-Done != prod-applied).

START PROTOCOL (in order):
1. Confirm you are in the FRONTEND repo: scripts/test-governance.ts EXISTS and
   scripts/recap_artifact_regenerate.py does NOT (both repos prompt `squadvault %` - this is the
   guard). Verify HEAD == 73833bc; if it moved, the brief is stale - flag, reconcile, proceed.
2. Branch sweep (expect main-only). Create a feature branch (e.g. feat/w1-inc2-member-captions).
3. FRESH prod object-existence probe on qcaxemuydxlzpzgnnnoa BEFORE any migration apply. Re-run the
   six-true probe AND confirm media_captions does NOT yet exist and 'media_caption' is NOT yet in the
   member_consent_events category CHECK. (The G11 false-pass lesson: a green gate can be green because
   the guarded object does not exist. Object-existence, not the schema_migrations ledger.)

READ before building (the build is measured against the spec, not this brief):
- engine 905cb1c _observations/OBSERVATIONS_2026_06_19_PHASE_11_W1_INC2_SPECIFICATION.md - sections 5
  (operational shape: the migrations, RLS, probe, surface), 6 (invariants), 7 (governance). This is
  the contract.
- engine 905cb1c _observations/OBSERVATIONS_2026_06_19_W1_INC2_SCOPE_RULING.md - the ratified
  D-W1I2-1..6 (especially D-W1I2-4, the separation payload framing).
- frontend reuse sources: supabase/migrations/011_w1_av_room.sql (the substrate: media_entries =
  ITEM layer, media_provenance_tag_events = human-ratified FACT layer, media_display_withdrawals with
  the nullable media_entry_id minted for THIS increment); 010_member_consent_events.sql (consent log +
  default-posture + member-only INSERT); 019_oral_history_testimony_consent.sql (the CHECK-widen
  idiom to mirror); 020_member_history.sql (append-only table idiom); 021_testimony_separation_probe.sql
  (the probe you re-point) + the G23 block in scripts/test-governance.ts (the gate you mirror).

THE BUILD (units in ORDER - order is the binding constraint, the L.3 build lesson; actual migration
filenames are the next free numbers in sequence, not literal "022a/b/c"):

UNIT 1 - media_caption consent CHECK-widen (FOUNDER-APPLIED).
  Write the migration that adds 'media_caption' to the member_consent_events category CHECK (mirror
  019 exactly: DROP + re-ADD the CHECK with the new value appended; no rendering_class; the
  class-iff-synth biconditional holds unchanged). This is a CHECK-widen on live consent infra =
  Charter section 7 founder-escalation. YOU PREPARE AND VERIFY; THE FOUNDER APPLIES via the Supabase
  SQL editor. Do NOT self-apply. After the founder applies, verify a media_caption GRANT row is
  accepted by the CHECK. (pbcopy the on-disk .sql for the founder - paste-fragmentation on long SQL,
  the L.3 lesson.)

UNIT 2 - media_captions append-only table + caption display-withdrawal path.
  Per spec 5.2: media_captions(id, media_entry_id FK->media_entries NOT NULL [the ALLOWED item attach
  point], author_user_id FK->auth.users NOT NULL, body text NOT NULL, provenance text NOT NULL DEFAULT
  'MEMBER_CAPTION' CHECK(provenance='MEMBER_CAPTION') [non-strippable value-pinned stamp], recorded_at,
  supersedes FK->media_captions). NO FK to media_provenance_tag_events, NO FK to any event-ledger
  table, NO trigger. RLS per spec 5.3: SELECT league-authenticated scoped THROUGH the parent
  media_entries row (the media_provenance_tag_events_select precedent); INSERT member-only
  (author_user_id = auth.uid(), no commissioner proxy); NO UPDATE, NO DELETE policy (append-only).
  Display-withdrawal: REUSE the existing media_display_withdrawals (do NOT mint a new class) - add the
  minimal caption-target path per spec 5.4 (nullable caption_id, OR reuse the nullable media_entry_id
  with a discriminator); pick the minimal append-only-preserving shape and RECORD the choice in the
  close-out.

UNIT 3 - caption_separation_probe() + G24.
  Re-point 021: a SECURITY DEFINER function (booleans only, STABLE, search_path = public, pg_catalog)
  asserting (i) media_captions exists; (ii) provenance present AND NOT NULL; (iii) NO FK from
  media_captions references media_provenance_tag_events OR the event-ledger set (artifacts,
  artifact_versions, approval_events, franchise_season_records, trophy_room_entries) - the ONLY
  permitted confrelid is media_entries; (iv) NO user (non-internal) trigger on media_captions;
  (v) missing object -> FALSE (fails closed, inverse-of-G11). Add G24 to scripts/test-governance.ts
  mirroring the G23 block (serviceClient.rpc('caption_separation_probe'), fail on any false boolean,
  pass on all-true).

UNIT 4 - capture + two-layer display surface (spec 5.6).
  Capture: a member-authored caption box on the A/V Room item view; the route checks the CURRENT
  media_caption GRANT (member_consent_current) BEFORE INSERT - GRANT-precedes-capture, route-enforced
  (the L.1 precedent: RLS gates ownership + append-only, the route gates the grant); absence = no
  capture (fail-closed). Display: the item view renders TWO visibly-distinct layers - the
  human-ratified PROVENANCE panel (verified facts, derived latest-non-withdrawn over
  media_provenance_tag_events) and, structurally separate, the "as remembered by [member]" CAPTIONS
  panel (each caption attributed; gated by current media_caption GRANT AND not-withdrawn). Never
  merged; no synthesized consensus; a caption is never styled or placed so as to read as a provenance
  tag (the two-layer rendering invariant, built here for the first time).

ACCEPTANCE (the proof gate - mirror the L.1 discharge rigor):
- G24 green; caption_separation_probe all-true on prod (both/all existence booleans true, provenance
  NOT NULL + value-pinned, only-media_entries FK, no trigger).
- No governance regression: G1-G23 still green.
- End-to-end on DEPLOYED routes as a real franchise-linked member: NEGATIVE (caption attempt with no
  current media_caption GRANT -> refused, nothing stored) AND POSITIVE (GRANT precedes the caption;
  body stored verbatim, attributed, append-only; renders in the visibly-distinct "as remembered by"
  panel, never merged into the provenance panel).
- Revocable-forward PROVEN: a REVOKE withholds the caption from DISPLAY while the captured row stays
  intact (never rewritten).
- If a real caption was authored for the proof, scrub the acceptance data post-proof (service role,
  the L.1/L.3 precedent); confirm prod clean.

BOUNDARIES (inherited, non-negotiable): facts append-only; narratives derived never fact-creating; AI
assists humans approve; silence over speculation; no analytics / optimization / engagement loops /
prediction; architecture frozen. Captions NEVER contaminate media_provenance_tag_events or the event
ledger (the structural payload). Provenance tags stay human-ratified, never AI-guessed. NO reaction
counts, NO engagement metrics on captions, ever. No AI-authored captions - the member writes.

HAZARDS TO HOLD:
- repo-Done != prod-applied: the FRESH probe (Step 3) before apply is non-negotiable (the 010 G11
  false-pass).
- CHECK-widen is FOUNDER-APPLIED (Unit 1): prepare + verify, never self-apply (019 precedent).
- Both repos prompt `squadvault %`: confirm FRONTEND before any write.
- Browser PR merge silently fails: merge via `gh pr merge` (CLI) after CI, never the browser button;
  tag-and-delete the merged branch.
- Long SQL paste-fragments: pbcopy the on-disk .sql file for the founder's SQL-editor apply.
- Member-keyed work (L.3 lessons): the URL slug is canonical_id (70985) not the UUID; franchises is
  RLS-gated (resolve via the admin/service path); author_user_id is the PERSON (auth.uid()).
- Native Write + git commit + gh; NOT the DECIDE-chat heredoc/pathlib/glob idioms.

PARKED (do not pick up): marginalia (the W.1 successor increment); self-tag (member_identification
self-application - a FACT-layer act, its own increment); the L.1 display successor (renders L.1
testimony, not media captions); W.2/W.3/W.5-taxonomy (overflow).

OUTPUT:
1. The build, on the feature branch, merged to frontend main via gh pr merge after CI + all gates +
   the acceptance proof.
2. Frontend ROADMAP.md flip + a discharge close-out memo in frontend _observations/ (record the
   display-withdrawal shape chosen in Unit 2, the actual migration numbers, the prod probe results,
   and the acceptance proof).
3. A small ENGINE doc-only commit updating docs/STATE.md: W.1 Inc 2 capture+display DISCHARGED (with
   the frontend hashes), docket item 4 -> DISCHARGED.

Opening prompt:
"EXECUTE session for W.1 Inc 2 (member captions: capture + two-layer display in the A/V Room),
FRONTEND build. Confirm you are in the frontend repo (test-governance.ts present,
recap_artifact_regenerate.py absent), verify HEAD == 73833bc, branch-sweep, cut a feature branch, and
run the FRESH prod object-existence probe on qcaxemuydxlzpzgnnnoa BEFORE applying anything - confirm
the six-true substrate AND that media_captions does not yet exist and 'media_caption' is not yet in
the consent CHECK. Then read the W.1 Inc 2 specification (engine 905cb1c,
_observations/OBSERVATIONS_2026_06_19_PHASE_11_W1_INC2_SPECIFICATION.md) sections 5-7 and the reuse
sources (011 substrate, 019 CHECK-widen idiom, 020 table idiom, 021 probe + the G23 block). Build in
order: (1) the media_caption consent CHECK-widen - PREPARE it, I apply it via the SQL editor, you
verify; (2) the media_captions append-only table + the caption path on the existing
media_display_withdrawals; (3) caption_separation_probe() re-pointed at the media FACT layer + G24;
(4) the capture route (GRANT-precedes-capture) + the two-layer display (verified provenance panel vs
visibly-distinct 'as remembered by' captions panel, never merged). Prove it end-to-end as a real
member (negative: no grant -> refused; positive: grant precedes caption, attributed + append-only,
renders distinct; revocable-forward: REVOKE withholds display, row intact), G24 green, no G1-G23
regression. Merge via gh pr merge, flip the frontend ROADMAP + close-out memo, then a small engine
STATE line discharging docket item 4. Git wins over the brief."
