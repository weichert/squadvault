# OBSERVATIONS 2026-06-10 - W.1 Mr. Herlth's A/V Room: Admission Record
## Four-memo chain, memo 4 of 4 (registration)

**Date:** 2026-06-10
**Session:** Fable DECIDE (Charter v1.0 section 2.1).
**Status:** RATIFIED + FILED 2026-06-10 (D-W1-1..6 as recommended). This memo is the
admission record (SAT v1 section 4.1: the per-surface constitutional memo chain IS the
native-admission record) and the filing/registration instruction set for the Opus filing
session (executed this commit series).
**Verified anchors at authoring:** engine `1782e3b` - frontend `248895c`.

---

## 1. Admission record

| Field | Value |
|---|---|
| Surface admitted | W.1 - Mr. Herlth's A/V Room (W1_AV_ROOM) |
| Admission kind | NATIVE (SAT v1 sections 2.2 / 4.1; the four-memo chain is the record) |
| Content classes admitted | media archive entry; provenance tag event; room ratification event; media testimony (caption/marginalium - specified, build gated on E2.3); display withdrawal (shared sibling class) |
| Channels | login-gated Clubhouse routes `/league/[id]/av-room` (+ `/ingest`, commissioner-only) |
| Gates satisfied | (a) four-memo chain - this chain; (b) Manual Fact Import frame - governed-testimony class formalized (memo 1 section 4; frame D1-D6 untouched and still OPEN); (c) W.6 - contract-card 7.2 declaration (2a derivation+publication; 2b publication; 2d capture+publication) |
| Decisions | D-W1-1..6 (memo 1 section 8) - ratified picks recorded below at ratification |
| HEADs at admission | engine `1782e3b`; frontend `248895c` (filing session updates to filing HEADs) |
| Founder ratification | 2026-06-10 - picks: D-W1-1 (a) D-W1-2 (a) D-W1-3 (a) D-W1-4 (a) D-W1-5 (a) D-W1-6 (a) - ALL AS RECOMMENDED (founder selection; Opus recorded per Charter 2.4). Filed at engine HEAD `1782e3b`. |

## 2. SAT registry addendum (to apply on ratification)

Per SAT v1 section 6 (registry additions are addenda), append to SAT section 5.1 native
admissions:

> | W.1 | Media archive entry; provenance tag events; room ratification; media testimony (2d, build gated on E2.3) | W.1 chain memos (this admission record) | Clubhouse `/league/[id]/av-room` |

Record in the addendum: this is the SAT's first invocation as governing reference for a
genuinely new surface's admission (native routing exercised); E1.7 disposition =
**DISCHARGED-NATIVE**; the SAT's cross-surface mechanism (4.2) remains unexercised and
the SAT remains provisional - its promotion gate is still the first cross-surface
admission (canonically `rivalry_chronicle_v1` -> E1).

## 3. Filing instructions (Opus filing session, engine repo, doc-only path)

1. Verify HEADs; confirm engine repo identity
   (`test -f scripts/recap_artifact_regenerate.py` TRUE).
2. File the four artifacts in `_observations/` (chain memos 1, 2, 4 under their
   OBSERVATIONS names; the contract card as `W1_AV_Room_Contract_Card_v1_0.md`).
   Provisional filings; no Map registration yet (promotion per spec section 8.4).
3. Record founder ratification: fill section 1's ratification row and memo 1 section 8's
   picks IN A SUPERSEDING RATIFICATION MEMO if any pick differs from recommended
   (supersession-then-fold-in pattern, precedent `c4b4436`); if all picks = recommended,
   the filing commit message records "ratified as recommended" (W.6 precedent).
4. SAT addendum per section 2 (separate dated addendum file or appended section per SAT
   section 6; one topic per commit).
5. STATE.md updates (same commit series): W.1 chain RATIFIED (hashes); E1.7 ->
   DISCHARGED-NATIVE with the cross-surface caveat; open item -> W.1 Increment 1
   execution brief (next); E2.3 noted as Increment 2's build gate.
6. Doc-only commits: ASCII subjects, banner/xtrace/allowlist/docs-Map gates, skip
   prove_ci, gates and commits as separate steps.

## 4. The build handoff (what the execution brief must contain)

Per Charter section 5, the Increment 1 execution brief (authored post-ratification, consumed
in Claude Code against the FRONTEND repo `~/squadvault`) must carry: verified frontend HEAD;
exact paths (migration `011_*` for the W.1 classes; `src/app/league/[id]/av-room/...`;
server-side upload/signed-URL routes); binary acceptance criteria derived from spec
sections 5-6 (including: RLS default-deny proven by a planted UPDATE/DELETE attempt test,
G-series style; fail-closed room render; 2a/2b/2d gates read `member_consent_current`;
photo-first ingest tooling); gates to run; OUT OF SCOPE = Increment 2 writes, AI anything,
W.2 aesthetics, engine changes; and hashes for every already-done claim (the consent view
exists at `010:72`; the withdrawal-class reuse check from spec 5.5).

## 5. What this chain leaves open (registered, not dangling)

- Frame D1-D6 (manual-source adapter): OPEN, untouched, founder's separate call.
- Increment 2 build: gated on E2.3; spec complete; zero further adjudication needed.
- W.2 aesthetic application to the room (VHS shelf et al.): W.2's chain.
- W.8 corpus-match proposals: W.8's chain; gains its corpus precondition at Increment 1.
- L.4 storage/playback reuse and L.1 testimony-class inheritance: their chains, inheriting
  memo 1 section 4 wholesale.
- SAT promotion: pending first cross-surface admission, unchanged.
