# Session Brief — Unit A8: Manual Source Adapter

Date authored: 2026-07-03 (DECIDE session; D-S ratified weekend-build)
Session type: EXECUTE (fresh session), three founder gates (⛔ G1: contract reconciliation + design; ⛔ G2: tests; ⛔ G3: diff + merge)
Repo: engine (weichert/squadvault) — identity test must PASS
Plan reference: Completion Plan v1.3 Unit A8; Manual_Source_Adapter_Contract_Addendum_v0_1_DRAFT_2026_06_23.md (project files / repo — locate and read); first dependent: KP 2018/12171 auction, provisional 0002/$67
Scope in one line: the governed entry path for commissioner-attested facts — human testimony entering the append-only ledger with ATTESTED provenance, never masquerading as canonical.

## Kickoff

You are an EXECUTE session for SquadVault Unit A8: the Manual Source Adapter. Read _observations/session_brief_unit_a8_manual_source_adapter.md in full, then the Manual Source Adapter Contract Addendum draft. CLAUDE.md ritual; three ⛔ gates. Hard rules: attested facts are append-only and carry COMMISSIONER_ATTESTED provenance — never CANONICAL; the adapter may never modify, supersede, or shadow a canonical fact (where an attested fact and a canonical fact conflict, canonical wins and the conflict is surfaced, not resolved); every attested entry records who attested and when; no silent ingestion — attestation is an explicit founder act per entry; tests founder-ratified before implementation; prod DB untouched until the founder's own apply step; nothing published.

## 1. Objective

Ship the Manual Source Adapter: the governed, tested entry path by which
commissioner-attested facts enter the append-only ledger under
COMMISSIONER_ATTESTED provenance. Concretely: (a) the schema for attested
fact rows with full provenance (who attested, when, on what basis),
carrying the same append-only/no-DELETE discipline as every sibling
table; (b) an entry tool (CLI/script per the ops-shim conventions) that
makes attestation an explicit, auditable founder act per entry — no batch
silent ingestion; (c) the branch-integrity guarantees, proven by tests:
attested facts never modify, supersede, or shadow canonical facts, and a
canonical/attested conflict is surfaced, never resolved by the adapter;
(d) the consumer-label audit and any label-path confirmations so every
surface rendering an attested fact shows the ATTESTED branch honestly.
The acceptance fixture is the KP 2018/12171 auction provisional
(0002/$67) entered in a scratch DB; its production entry remains a
separate founder act gated on KP-sheet confirmation. The deliverable is
the adapter, its tests, and the ratified contract text as the addendum
draft's successor — the door for testimony, built to the same standard
as the vault it opens into.

## 2. Constitutional ground

Two-branch trust model: CANONICAL (derived, gold) and COMMISSIONER_ATTESTED (testimony, ATTESTED label) — the Founder's Seal precedent. The adapter is the governed door for the second branch: same dignity as oral history, same append-only ledger, honestly labeled. Silence over speculation applies: an unattested gap stays a gap; the adapter never infers.

## 3. Constraints

- Contract first: Gate 1 reconciles the design against the v0.1 addendum draft; deviations are proposed to the founder, never silently adopted. The ratified design is the addendum's successor text.
- Scope of fact classes: exactly those the addendum enumerates plus what the KP 2018 case requires (auction acquisition amount); no speculative classes.
- Provenance schema parity: attested rows carry the same append-only, no-DELETE, RLS-equivalent discipline as every sibling table.
- The KP case as fixture: the 2018/12171 provisional (0002/$67) is the acceptance fixture — entered via the adapter in a scratch DB, verified rendering as ATTESTED, never contaminating canonical A2 records. Its prod entry remains a founder act post-merge, gated on KP-sheet confirmation.
- Derived readers respect the branch: any consumer surfacing attested facts must label them; Gate 1 enumerates which existing consumers are affected (expected: draft/auction surfaces) and confirms label paths.

## 4. Procedure

Step 0 — Ritual + reading. Fresh clone, HEAD, identity, trio green, prod hash recorded. Read the addendum draft, the Founder's Seal implementation (migration 031 pattern), and the A2 substrate the KP case touches.
Step 1 — Design + reconciliation (no code). The adapter's shape (entry script/CLI per the ops-shim conventions, schema DDL, provenance fields), reconciled clause-by-clause against the addendum; the consumer-label audit; the test plan. ⛔ Gate 1.
Step 2 — Tests first. Ratified test plan implemented red where appropriate. ⛔ Gate 2 (may fold into G1 at founder discretion if the plan is fully specified).
Step 3 — Implement + prove. Trio green; prove_ci exit 0; scratch-DB KP fixture walkthrough documented; memo per conventions. ⛔ Gate 3 — diff + merge (commit series, founder messages, PR, squash; STATE line).

## 5. Acceptance criteria

Adapter matches the ratified contract text exactly; KP fixture enters scratch as ATTESTED and canonical A2 records are byte-unchanged; append-only discipline proven in tests; all affected consumers label the branch; trio + prove_ci green; prod DB hash unchanged by the session (founder applies separately).

## 6. Out of scope

Entering the KP fact into prod (founder act, post-KP-confirmation) · new fact classes beyond the ratified set · canonical-branch changes · the 2019/2020 FAAB back-fill (future founder decision) · renaming test_cavallini_mahomes_2018_qb_anchor_regression (fold into A4) · no frontend changes.
