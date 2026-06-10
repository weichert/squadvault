# Session brief - W.6 Consent Governance Memo (Fable DECIDE session)

Authored: 2026-06-10 (Claude Code, Opus). Detailed version folded in at HEAD `28e6b62`
(supersedes the lean version at `ef01b2a` / `07e65c3`).
Consumer: a Fable chat DECIDE session (Charter v1.0 section 2.1). This is a session-kickoff
prompt for a constitutional memo, NOT an execution brief - W.6 produces a governing frame,
not commits. Paste the block below into the Fable chat to start the session.

---

SquadVault - Fable DECIDE session - Unit W.6: Consent Governance Memo (constitutional)

=== ROLE & ROUTING ===
This is a Fable DECIDE session (Charter v1.0 section 2.1). The output is a CONSTITUTIONAL
MEMO that other sessions and the W.1 / W.4 / L.1 / L.3 / L.4 / W.8 chains will obey - not
code, not an execution unit. Authored in chat, not Claude Code. Distrust this brief; verify
every claim against the repos before designing on top of it.

=== START PROTOCOL (in order, before any proposal) ===
1. Read CLAUDE.md (Working Process Charter v1.0) in full.
2. Read docs/STATE.md and docs/SquadVault_Product_Document_of_Record_v2_1.md (DoR v2.1) -
   in particular Part 3 (W.6 + the track's standing law), Part 4 (L.1/L.3/L.4 - the
   downstream consumers), Part 6 (decision register), and Part 8 (the prohibitions).
3. Verify against git. Verified anchor at authoring: engine HEAD = 28e6b62. Confirm current
   HEAD; if this brief conflicts with git, GIT WINS - flag it before proceeding. Any brief
   claim without a hash is UNVERIFIED until you check it.

=== VERIFIED CONTEXT (with hashes) ===
- W.7 (framing drift-flag memo) shipped at 07e65c3 - first Track W item done.
- This brief itself: 28e6b62 (the prior version ef01b2a was sharpened with the consent-
  location finding below).
- W.6 is the LAST remaining "Now -> July" master-sequence item (DoR Part 7). Per D-L the
  track entry is "W.7 + W.6 immediately; W.1 first build" - so W.6 is the gate before W.1
  (the A/V Room) can begin.

=== WHY THIS MATTERS NOW (the dependency gate) ===
W.6 is a HARD PREDECESSOR to nearly the entire warmth/lore track. Until it is ratified,
none of the following may build:
- W.1 - attribution-level photo/video captions (the governed-testimony fact class).
- W.4 - the press-conference artifact class.
- W.8 - testimony-derived wall placement with provenance receipts.
- L.1 - the Historian Interviews (all ten members' attributed oral history).
- L.3 - The Vault (sealed-letter reveal mechanics; consent captured at writing). NOTE L.3's
  hard calendar anchor: it must ship before the 2026 draft (August) to capture this season's
  letters, and L.3 depends on W.6 - so W.6 is on the critical path to that deadline.
- L.4 - The Answering Machine (recorded voice testimony).
- Any audio rendering class.
Getting W.6 right and getting it soon both matter.

=== THE MANDATE (verbatim scope, DoR Part 3 W.6) ===
Author the consent model for: member LIKENESS, RECORDED VOICE, SYNTHESIZED VOICE, ATTRIBUTED
QUOTES, and MEDIA APPEARANCES. The model must be: captured once; ratified PER-MEMBER;
append-only; and REVOCABLE-FORWARD (revocation stops future use and NEVER rewrites the past
record).

=== SUBSTRATE VERIFICATION (a brief claim to check before designing) ===
The DoR says W.6 "extends founding_sessions.consent." That table/field is NOT in the ENGINE
repo storage layer (schema.sql / migrations show nothing at 28e6b62). The DoR locates it
elsewhere: Part 1.2 lists "full founding session" as a SHIPPED FRONTEND route (with G-series
governance tests + RLS, no-DELETE policies), and L.1 says member interviews "reuse founding-
session machinery (exchanges jsonb, consent, topic coverage)." So consent state lives in the
founding-session machinery in the FRONTEND/Supabase repo (weichert/squadvault-frontend),
NOT the engine. Verify its current shape THERE before specifying the extension - do not design
against the engine schema, and do not assume the field's form. (Charter hazard: "data correct
on prod is not the same as the code path being guarded in the repo - verify at the layer the
claim is about.")

=== CONSTITUTIONAL CONSTRAINTS (non-negotiable) ===
- Standing law, Tracks W & L (DoR Part 3): "member words can become facts (attributed,
  consented, append-only); member behavior is never measured. No telemetry, no autonomous
  publication, no engagement loops."
- DoR Part 8: "No likeness or voice synthesis ahead of W.6." (W.6 is the gate that Part 8
  names - this memo is what lets synthesis ever be considered, and it must set that bar.)
- Charter Authority line: "No analytics, optimization, engagement loops, or prediction - ever."
- L.1's constitutional shape, which W.6 must stay consistent with: testimony is a
  fact-ABOUT-WHAT-WAS-SAID; it never contaminates the event ledger. Verified facts and
  remembered accounts render as visibly distinct layers. Consent governs the testimony layer;
  it must not create a path that mutates the immutable factual ledger.
- AI assists; humans approve publication. Facts are immutable and append-only.

=== MAP EACH CONSENT SURFACE TO ITS CONSUMER (so the model is concrete, not abstract) ===
- LIKENESS -> W.1 photo/video tagging; W.8 generated-art boundary ("no member likeness in
  generated art ahead of W.6"); W.4 press-conference class.
- RECORDED VOICE -> L.4 Answering Machine (recording members - the safest audio case).
- SYNTHESIZED VOICE -> the separately-gated post-W.6 "league radio" rendering class. Most
  sensitive; Part 8 forbids it until W.6 expressly governs it.
- ATTRIBUTED QUOTES -> W.1 captions; L.1 interview accounts; L.3 letters at reveal; W.8
  tappable wall-provenance receipts ("hung here because Robb told the historian, March 2026").
- MEDIA APPEARANCES -> the W.1 A/V corpus (existing photos/videos of members).

=== OPEN DECISIONS THE MEMO MUST ADJUDICATE (frame as D-x; the founder picks - never assume) ===
1. Scope taxonomy: are the five surfaces above SEPARATE consent categories, each independently
   grantable and revocable, or a bundle? (Recommend reasoning toward independent grants -
   synthesized voice in particular should be opt-in-able separately from recorded voice.)
2. "Captured once, ratified per-member" - what that means mechanically, and how it composes
   with the four-memo chain / Surface Admission Test and the Manual Fact Import frame.
3. Revocable-forward semantics - the hardest question. Define UNAMBIGUOUSLY how revocation
   stops FUTURE use while leaving the append-only past record intact, including: already-
   published artifacts (do they remain as historical record, get withdrawn from future
   re-rendering, or both?), and how this reconciles with the immutable-fact / no-rewrite-the-
   past discipline.
4. Record shape & location: the append-only consent event form, where it lives (per the
   substrate finding above), and the ratification surface (who acts, what they see, what is
   recorded). Confirm RLS / no-DELETE parity with the founding-session machinery.
5. Granularity of ratification: room/league-level vs item-level (cross-ref W.1's room-level
   consent ratification and member-caption testimony class).
6. Default posture: in the absence of explicit consent, the system does WHAT? (Silence-over-
   speculation suggests: no use. State it as law.)

=== HARD BOUNDARIES / OUT OF SCOPE ===
- BUILD NOTHING. No schema migrated, no surface built. W.6 produces the governing frame a
  later Claude Code unit implements against.
- Do not re-litigate adjudicated decisions (Part 4A / Vision Register) without founder
  instruction. If framing drifts toward engagement/optimization/measurement language, NAME it
  and stop (cert-5 discipline - catching drift is a success, not an embarrassment).
- The founder approves the memo before it is binding. Numbered decisions get an explicit
  founder pick.

=== DELIVERABLE ===
A constitutional memo (the binding W.6 consent-governance frame) suitable for founder
ratification, containing at minimum:
  (a) the consent taxonomy and per-surface model;
  (b) capture-once / per-member ratification mechanics;
  (c) the revocable-forward rule, stated precisely enough to implement, with the
      already-published-artifact case resolved;
  (d) the append-only record shape and where it lives (post-verification);
  (e) the default-no-consent posture;
  (f) explicit consistency statements against the standing law, Part 8, and L.1's
      testimony-never-contaminates-the-ledger shape;
PLUS a clean list of the D-x decisions you surfaced for the founder to pick before any
implementation unit is briefed.

---

Author's note (Claude Code, for the founder, not part of the paste block):
- The DoR's "extends founding_sessions.consent" claim has no engine-repo backing (no such
  table/field in schema.sql or migrations as of 28e6b62). DoR 1.2 + L.1 locate consent in
  the shipped founding-session machinery in the FRONTEND repo; the prompt points Fable there
  to verify its shape before designing. The home is inferred from the DoR's own
  cross-references, not asserted - the stale-claim hazard still applies until Fable confirms.
- "Cavallini revocation" in STATE.md is ANCHOR revocation (a falsified narrative anchor
  purge), unrelated to consent revocation - deliberately not cited here.
- The consent-surface -> consumer map and the L.3 critical-path note are the detail upgrades
  over the lean version; they force the memo to design against concrete use, not abstractions.
- Design choices are framed as open questions for Fable + the founder to adjudicate, not
  pre-decided in Claude Code.
