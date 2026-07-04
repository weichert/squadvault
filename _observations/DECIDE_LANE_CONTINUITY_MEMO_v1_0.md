# DECIDE-Lane Continuity Memo v1.0

Ratified: founder, 2026-07-04. Occasion: the current DECIDE-lane adjudicator (Claude Fable, this chat) is unavailable after 2026-07-07; this document is what the next adjudicator reads first.

## 1. What this document is

The project prompt holds the invariants; STATE.md holds the current facts; the memos hold the history. This document holds the craft — how gates are actually adjudicated, which hazards recur, what the founder expects of this chair, and why the open items are sequenced as they are. Read the project prompt, then this, then STATE.md at HEAD, in that order. Everything here is advisory except where it quotes a ratified ruling; ratified rulings bind until the founder amends them.

## 2. The role

The DECIDE lane adjudicates, ratifies, authors briefs, and keeps institutional memory. It never writes to repos or databases. Its outputs are: decisions with reasoning, briefs committed to _observations/ before the sessions that run them, gate adjudications, and append-only corrections when it is wrong — which it will be. The founder delegates judgment expecting a grounded recommendation with reasoning, not a menu of questions; he ratifies in a word when the frame is right and pushes back plainly when it isn't. The EXECUTE lane (Claude Code) is capable and disciplined but stateless and literal: it will resurface settled decisions as open items, follow a wrong brief off a cliff if the brief says to, and halt beautifully when told what a halt is for. The gates between the lanes are where quality lives.

## 3. Gate craft

Every unit ships through named ⛔ gates. What each kind is for:

**Pre-registration gates (measurements):** the block must demonstrably predate results — cell lists drawn by seeded code included verbatim, readout SQL written before data exists, config read from files at HEAD rather than memory. Once ratified it is frozen; the only permitted deviation is a recorded one (INELIGIBLE_POST_PIN), never a substitution. If results later force reinterpretation, the frozen rule's own clauses (catch-alls, tolerances) are applied transparently — all passes shown, every moved classification quoted and evidenced — and the rule itself is never edited.

**Design/plan gates (before code):** the questions that matter are premise and joint. Premise: does the plan's factual basis survive contact with git and the data? (Verify against HEAD; the plan's author may be working from a stale copy — including the brief itself.) Joint: where does new code touch old paths? The new module reads itself; the refactored consumer is where regressions live.

**Test gates:** outcomes freeze at ratification. Additions are always permitted; expected-outcome changes never are — with one narrow exception ratified by precedent: repairing a fixture's own internal inconsistency (reconstruction padding contradicting the classification it encodes) is fixture repair, not outcome change, and the memo must carry the reasoning.

**Diff gates (before merge):** read the hot paths hardest — any file carrying frozen baseline behavior (the verifier especially) must show additive-only diffs with byte-identity proof (regeneration of existing artifacts). Commit messages are founder-written: draft them for his wording pass, ASCII subjects, no Co-Authored-By. STATE lines are one-line unit summaries with a memo pointer (ratified D-T), not abstracts.

The universal rule: halt-don't-guess. A stopped session costs an hour; a guessed gate costs the record. When an EXECUTE session halts on a contradiction, the halt is the system working — thank it, diagnose in the DECIDE lane, and send back an adjudication, not an improvisation.

## 4. Standing hazard register

1. Stale-brief hazard: briefs age from the moment of authorship — a 48-hour-old brief was materially wrong twice this week (F2 premise; A8 schema model). Git wins over briefs, chat, and memory; the EXECUTE session's verification is the correction mechanism, not an insult.
2. Checklist-vs-text drift: the author's most repeatable error — completeness checklists written before the final text missed sections twice (F1, A8: both dropped ## 1. Objective). Derive the checklist from the final text as the last authoring step. Expect to make this mistake anyway; the check catches its own author, which is the point.
3. Stale-memory carry-forward: cross-session memories resurface settled items as owed work (the DoR:58 false carry-forward; the seed-004/migration-031 "pending" ghost). Before acting on any remembered obligation, verify it against git and STATE.
4. Stacked-squash PR traps (frontend): never --delete-branch mid-stack (closes children); reopen requires resurrecting the exact base branch name at its recorded tip; after retargeting, the Files-changed view lies — the only honest diff is a local git merge --squash --no-commit test merge; children carrying already-squashed originals genuinely conflict — destack with rebase --onto <main> <original-parent-tip>; retarget children before deleting their base. PR #48's destack anchor is recorded in its brief.
5. Clipboard/channel failures: the founder's copy path from terminals fails silently and emits stale payloads; briefs travel inside landing instructions with completeness checks, never by reference; reports travel by session-unique Desktop file (byte count confirmed in chat is ground truth — Finder views can lag on sync).
6. Repo identity: both clones historically prompted squadvault %; the engine test is test -f scripts/recap_artifact_regenerate.py (PASS = engine). The frontend's canonical clone is now /Users/steve/projects/squadvault-frontend; an older clone named squadvault is flagged-for-deletion, never used.
7. CC cannot see dashboards: Supabase and Vercel config states are founder-visible only; never trust an EXECUTE session's claims about them, and never let it mark founder dashboard steps as done.
8. Prod-hash discipline: every engine session touching data records the prod DB hash at start and end; scratch copies for anything generative; prod entry of facts is always a founder act.
9. .gitignore echoes: the squadvault/ pattern trap was permanently fixed in A8's commit series, but pattern-anchoring bugs of this class recur — a new module silently ignored is diagnosed by git status showing less than you built.
10. Environment artifacts masquerading as regressions: placeholder Supabase URLs make the frontend governance suite fail 7/19 (DNS, not Postgres) and block bare-clone builds (/auth/login prerender finding, registered). A red gate on a doc-only diff is an environment question first.

## 5. The working relationship

The founder ratifies fast ("Approved. Let's go!!"), works in marathons when moved, and expects the chair to hold the calendar and the register so he doesn't have to. Push back with reasoning when he's about to act on a false premise — he corrects course in one message and values the catch. Nag sparingly but persistently on founder-only acts (the league note survived three days of it). When he's torn, locate the actual tension (fatigue, scope-treadmill fear, product doubt) rather than re-arguing the engineering. When he says "proceed at your direction," give direction — with the reasoning attached so his ratification is informed, never blind. And when this chair is wrong, say so first, plainly, and record the correction append-only; the week's record shows the system catching its own author repeatedly, and that is its best property.

## 6. The open register (with reasoning)

- Unit 1.7b (presentation implementation + lint): brief landed 4554ff6, gates written for successor adjudication (its §2 tells you what each gate is for). Execute August, pre-Week-1. This is what closes R5; do not let "E1.5b closed R5" reconciliations confuse it.
- Unit A9 (2018 auction de-contamination): registered in STATE; the duplicate-win evidence (rows 3877/3891/3892) is in A8's memo; the KP-sheet adjudicates the true winner. Needs a DECIDE-authored brief when picked up.
- KP prod entry: founder act via the A8 CLI, gated on KP-sheet confirmation — routes through A9's resolution first if the sheet shows the 0002/$67 row is the contested one.
- Prose-capture unit (SUPERLATIVE/STREAK attribution): capture list in the P1 memo; auto-deferred past Week 1 by ratified ruling — do not reopen without explicit founder word.
- Runbook trigger 07-18: pre-authorized kickoff to be landed alongside this memo (companion document).
- League note: founder publishing act; if still unposted, it is the register's oldest item and the only one that ships to humans.
- Frontend papercuts, registered not urgent: /auth/login prerender env dependency; per-page OG metadata (link unfurls) — pairs naturally as one half-session before invites.
- Slimmed A4 (engine doc hygiene): the 19-vs-14 verifier enum in docs; DoR §1.1 staleness; STATE trim to D-T style; the Cavallini/Mahomes test rename; D-R's scripts/ soft lint tier folds in here.
- W.4 Writer's Room: Window D, mid-season at earliest, after weekly rhythm is stable — resist pulling it forward; the plan's reasoning (don't build the pitch factory before the assembly line has run) held against founder enthusiasm once already.
- Phase 11 Closure Memo: six certifications, gated on NFL Week 1 — the closing act of the current phase.

## 7. The calendar

07-18: pre-season runbook trigger (operational, no software). ~08-15: Draft Weekend — the natural moment for the nine invites, with the frontend invite chain, consent page, and coach offices verified ready. ~09-08: NFL Week 1 — first live cycle; the season starts at the RM1-measured rate, constitutionally safe (silence, not error); 1.7b should be landed before it so the group text receives clean prose. Post-Week-1: prose-capture eligibility resumes; Phase 11 closure certifications begin.

## 8. Lessons with receipts

The week that produced this memo shipped a measurement baseline, a two-stage attribution that inverted its own hypothesis, a verifier fix that did exactly what the evidence predicted, a re-measurement that validated it, a testimony door built against a ratified contract that overrode its own brief, and a presentation contract for the season's voice — through gates that caught the author's errors at least four times (two dropped Objective sections, one falsified premise, one stale schema model). The lesson is not that the author errs; it is that the process converts error into record instead of product damage. Guard the gates, verify at HEAD, correct append-only, and remember that for a vault whose promise is trustworthy memory, the system is the product.
