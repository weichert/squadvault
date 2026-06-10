# Session brief - W.6 Consent Governance Memo (Fable DECIDE session)

Authored: 2026-06-10 (Claude Code, Opus) at HEAD `07e65c3`.
Consumer: a Fable chat DECIDE session (Charter v1.0 section 2.1). This is a session-kickoff
prompt for a constitutional memo, NOT an execution brief - W.6 produces a governing frame,
not commits. Paste the block below into the Fable chat to start the session.

---

SquadVault - Fable DECIDE session - Unit W.6: Consent Governance Memo (constitutional)

ROLE & ROUTING. This is a Fable DECIDE session per Charter v1.0 section 2.1: the output is
a constitutional memo that other sessions (and the W.1/W.4/L.1/L.3/L.4 chains) will obey.
It is authored in chat, not Claude Code. Distrust the brief; verify before proposing.

START PROTOCOL (do this first, in order):
1. Read CLAUDE.md (the Working Process Charter v1.0) in full.
2. Read docs/STATE.md and docs/SquadVault_Product_Document_of_Record_v2_1.md (DoR v2.1).
3. Verify this brief against git. Verified anchor at authoring: HEAD = 07e65c3
   ("docs(observations): W.7 framing drift-flag memo"). Confirm HEAD; if the brief
   conflicts with git, git wins - flag it before proceeding. Brief claims without hashes
   are UNVERIFIED.

VERIFIED CONTEXT (with hashes):
- W.7 (framing drift-flag memo) shipped at 07e65c3 - the first Track W item is done.
- W.6 is the LAST remaining "Now -> July" master-sequence item (DoR Part 7). D-L sequenced
  "W.7 + W.6 immediately; W.1 first build" - so W.6 is the gate before W.1 (the A/V Room)
  can begin its build.
- W.6 is a HARD PREDECESSOR to: W.1 attribution-level captions, the W.4 press-conference
  artifact class, L.1 (Historian Interviews), L.3 reveal mechanics, L.4 (Answering Machine
  audio testimony), and any audio rendering class. Nothing touching member likeness, voice,
  or attributed words may build until W.6 is ratified (Charter section 7).

THE TASK. Author the W.6 Consent Governance Memo. Per DoR Part 3, W.6 is the consent model
for: member likeness, recorded voice, SYNTHESIZED voice, attributed quotes, and media
appearances. The model must be: captured once; ratified PER-MEMBER; append-only;
REVOCABLE-FORWARD (revocation stops future use and NEVER rewrites the past record).

SUBSTRATE VERIFICATION (a brief claim that needs checking before you design on top of it):
- The DoR states W.6 "extends founding_sessions.consent." That table/field is NOT present
  in the ENGINE repo storage layer (schema.sql / migrations show nothing at 07e65c3). The
  DoR locates it elsewhere: Part 1.2 lists "full founding session" as a SHIPPED FRONTEND
  route (with G-series governance tests + RLS), and L.1 says the Historian Interviews
  "reuse founding-session machinery (exchanges jsonb, consent, topic coverage)." So consent
  state lives in the founding-session machinery in the FRONTEND/Supabase repo
  (weichert/squadvault-frontend), not the engine. Verify its current shape THERE before
  specifying the extension - do not design against the engine schema or assume the field's
  form. (Charter hazard: "data correct on prod is not the same as the code path being
  guarded in the repo - verify at the layer the claim is about.")

CONSTITUTIONAL CONSTRAINTS THE MEMO MUST HONOR (non-negotiable):
- Standing law, Tracks W & L (DoR Part 3): "member words can become facts (attributed,
  consented, append-only); member behavior is never measured. No telemetry, no autonomous
  publication, no engagement loops."
- DoR Part 8 prohibitions, esp.: "No likeness or voice synthesis ahead of W.6."
- Charter Authority line: "No analytics, optimization, engagement loops, or prediction - ever."
- Facts are immutable and append-only; AI assists, humans approve publication.

OPEN QUESTIONS THE MEMO SHOULD ADJUDICATE (frame as decisions; numbered D-x get an explicit
founder pick - do not assume):
1. Scope taxonomy: are likeness / recorded-voice / synthesized-voice / attributed-quotes /
   media-appearances separate consent categories, each independently grantable and
   revocable, or one bundle? (Synthesized voice is the most sensitive - Part 8 gates it.)
2. Capture-once vs per-use: what "captured once, ratified per-member" means mechanically,
   and how it interoperates with the four-memo chain / Surface Admission Test and the
   Manual Fact Import constitutional frame.
3. Revocable-forward semantics: precisely how revocation stops FUTURE use while leaving the
   append-only past record intact - including already-published artifacts (do they remain,
   get withdrawn from future rendering, or neither?). Define the boundary unambiguously.
4. Record shape: where consent state lives, its append-only event form, and the ratification
   surface (who acts, what they see, what is recorded).
5. Per-member ratification at room/league level vs item level (cross-ref W.1's room-level
   consent ratification and member-caption testimony class).

ESCALATION / OUT OF SCOPE:
- Do NOT build anything. This is a constitutional memo, not an execution unit. No schema is
  migrated and no surface is built in this session; W.6 produces the governing frame that a
  later Claude Code unit implements.
- Do NOT re-litigate adjudicated decisions (Part 4A / Vision Register) without founder
  instruction. If the work drifts toward engagement/optimization language, name it
  (cert-5 discipline) and stop.
- The founder approves the memo before it becomes binding. Numbered decisions get an
  explicit founder pick.

OUTPUT: a constitutional memo (the binding W.6 governance frame), ready for founder
ratification, plus a clear list of any D-x decisions you surfaced for the founder to pick.

---

Author's note (Claude Code, for the founder, not part of the paste block):
- The DoR's "extends founding_sessions.consent" claim has no engine-repo backing (no such
  table/field in schema.sql or migrations as of 07e65c3). DoR 1.2 + L.1 locate consent in
  the shipped founding-session machinery in the FRONTEND repo; the prompt now points Fable
  there to verify its shape before designing. The home is inferred from the DoR's own
  cross-references, not asserted - the stale-claim hazard still applies until Fable confirms.
- "Cavallini revocation" in STATE.md is ANCHOR revocation (a falsified narrative anchor
  purge), unrelated to consent revocation - deliberately not cited here.
- Design choices are framed as open questions for Fable + the founder to adjudicate, not
  pre-decided in Claude Code.
