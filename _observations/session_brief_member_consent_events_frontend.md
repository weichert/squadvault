# Implementation brief - `member_consent_events` (frontend unit, W.6 D-V)

Authored: 2026-06-10 (Claude Code, Opus), engine HEAD `df09a5e`.
Target repo: `weichert/squadvault-frontend`, at `~/squadvault` (current `main`, `4e44bb3`).
REPO-CONFIRM before the first write: `test -f scripts/recap_artifact_regenerate.py` must
FAIL here (engine-only marker; BOTH repos prompt as `squadvault %` - this is the exact
confusion the charter's repo-confirmation check exists for).
Builds against: the RATIFIED W.6 Consent Governance Memo
(`docs/SquadVault_W6_Consent_Governance_Memo_v1_2.md`, engine `df09a5e`). All design is
decided there (D-S..D-X); this brief is the repo-grounded EXECUTE translation, NOT new
constitutional design. Where this brief and W.6 differ, W.6 governs.

## Routing / process (RESOLVED by founder 2026-06-10)

- **EXECUTE, standard Opus build in the frontend repo - no Fable spec chain.** W.6 is ratified
  (`df09a5e`); the governing frame is settled, so a Fable chain would have nothing to
  adjudicate. The frontend's lighter local process is fine - the governance weight here lives
  in the G-series RLS tests and append-only posture this brief specifies, not in prove_ci.
- **Implementation of W.6, NOT a new surface - build straight against this brief.** The SAT /
  four-memo chain exists to constitutionally admit new expressive surface area (things that put
  content before the league); the consent panel is the ratification MACHINERY that W.6 section
  5 (D-V) already specified in detail. A chain would re-adjudicate questions the memo answered.
  Precedent: the founding-session consent panel shipped as governance machinery inside the
  founding arc, not via its own admission. Section 7.2's chain clause targets surfaces that
  CONSUME consent (W.1, W.4, W.8, the L-units) - this is the substrate they read.
- **CONDITION (keeps the discipline visible):** the build's close-out still carries a
  7.2-style declaration - which section-2 categories it touches and at which gates - even
  though it IS the consent system itself. Costs a paragraph; makes the pattern uniform for
  every chain that follows.

## Verified repo facts (read at `4e44bb3`; do not re-derive, but re-confirm if `main` moved)

- Member identity: there is NO `members` table. A member is an `auth.users(id)` linked via
  `franchises.member_user_id` (`001_core_schema.sql:48`). `get_user_league_id()`
  (`003_rls_policies.sql:24`) derives a user's league from their franchise.
- RLS helpers (`003`): `get_user_league_id()`, `is_commissioner(p_league_id)` (`:37`),
  `is_admin()` (`:51`) - all `SECURITY DEFINER STABLE` sql.
- Append-only sibling = `approval_events` (`003:148-167`): SELECT + INSERT policies only, NO
  UPDATE/DELETE; INSERT WITH CHECK enforces `actor_user_id = auth.uid()` (admin cannot proxy).
  This is the governance precedent to mirror for "only the member can grant."
- No-rewrite mechanism is RLS default-deny (W.6 Appendix A): enable RLS, grant SELECT+INSERT,
  grant nothing else. Do NOT write explicit deny policies (no sibling does).
- API route template: `src/app/api/founding/[sessionId]/consent/route.ts` (SSR client,
  `auth.getUser()`, body validation, typed Insert via `Database['public']['Tables'][...]`).
- Types are hand-maintained in `src/lib/supabase/types.ts` (e.g. `ConsentRecord` :239).
- New tables get registered in the "Database allow-list" (precedent `aef6d0d`,
  "register franchise_season_records in Database allow-list") - a DB-shape guard/test.
- Migrations run 001-009; next is `010`. Confirm no new migrations landed on `main` first.

## Scope

**MVP (unblocks W.1 photo-consent reads and L.3's pre-August deadline):**
the event table + append-only RLS + derived current-state read + member grant/revoke surface
+ commissioner read-only state at the gates. This is the buildable unit.

**Fast-follow (same unit or immediate successor):** the display-withdrawal sibling
(W.6 section 4 / D-U) - only consumed by published-artifact surfaces (W.4/W.8/Almanac) that do
not exist yet, so its UI can lag. Include the table; defer the withdrawal UI.

**Separate engine unit (NOT this brief):** the engine allowlist consumption (W.6 7.3) -
the engine receives a deterministic allowlist derived from current consent and the verifier
checks attributed output against it (the FAAB-allowlist pattern,
engine `src/squadvault/core/recaps/context/writer_room_context_v1.py:456`). Cross-repo;
this brief only exposes the read (below). Interface contract stated; plumbing is engine work.

## Deliverables

### 1. Migration `010_member_consent_events.sql`

Proposed shape (exact DDL is the implementing session's; bind to W.6 section 5):

```
CREATE TABLE member_consent_events (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  member_user_id  uuid REFERENCES auth.users(id) NOT NULL,
  league_id       uuid REFERENCES leagues(id)    NOT NULL,
  event_type      text NOT NULL CHECK (event_type IN ('GRANT','REVOKE')),
  category        text NOT NULL CHECK (category IN
                    ('media_appearance','recorded_voice','likeness_derived',
                     'attributed_quotes','synthesized_voice')),
  rendering_class text,                         -- required iff category='synthesized_voice'
  context         text NOT NULL,                -- member_office_settings|l1_interview|l3_compose|l4_recording|...
  note            text,
  recorded_at     timestamptz NOT NULL DEFAULT now(),
  CHECK ((category = 'synthesized_voice') = (rendering_class IS NOT NULL))
);

ALTER TABLE member_consent_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "member_consent_events_select" ON member_consent_events
  FOR SELECT USING (
    member_user_id = auth.uid() OR is_commissioner(league_id) OR is_admin()
  );

-- INSERT is MEMBER-ONLY. Deliberately NO is_admin()/is_commissioner() here:
-- W.6 section 1.3 - the commissioner cannot proxy a grant for another member.
CREATE POLICY "member_consent_events_insert" ON member_consent_events
  FOR INSERT WITH CHECK ( member_user_id = auth.uid() );

-- NO UPDATE policy, NO DELETE policy. Append-only via RLS default-deny (D-V).
```

Notes the implementing session must honor:
- `league_id` is carried for the commissioner read-scope and matches the single-league reality
  + sibling pattern. The TRUE subject is `member_user_id` (person, not franchise; W.6 1.2).
  Cross-league/global consent semantics is a FUTURE question (vertical-expansion thesis) -
  OUT OF SCOPE; do not design for multi-league now, but do not preclude it.
- Place CHECK-constraint additions consistent with `002_constraints_and_triggers.sql` style if
  the repo separates constraints from table creation; otherwise inline as above.

### 2. Derived current-state read (W.6 1.1 - "derived, never stored mutable state")

A view `member_consent_current` (latest event per member+category+rendering_class):

```
CREATE VIEW member_consent_current
WITH (security_invoker = true) AS         -- so base-table RLS applies to the reader (PG15+)
SELECT DISTINCT ON (member_user_id, category, coalesce(rendering_class,''))
  member_user_id, league_id, category, rendering_class,
  event_type AS current_state, recorded_at
FROM member_consent_events
ORDER BY member_user_id, category, coalesce(rendering_class,''), recorded_at DESC;
```

- A current grant exists IFF a row exists with `current_state = 'GRANT'`. **Absence of a row =
  ungranted** (default-posture law, W.6 1.4) - consumers MUST treat missing as no-grant.
- DECISION for the implementing session: confirm `security_invoker` is available (Supabase PG
  version). If PG < 15, use a `SECURITY INVOKER` function or a policy-bearing equivalent so the
  member/commissioner RLS carries through - the read must NOT leak one member's state to
  another.

### 3. Types + Database allow-list

- Add a `MemberConsentEvent` interface and the `member_consent_events` Tables entry
  (Row/Insert/Update) to `src/lib/supabase/types.ts`, matching the `ConsentRecord`/sibling style.
- Register `member_consent_events` (and the view) in the Database allow-list per `aef6d0d` so
  the DB-shape guard passes.

### 4. API routes (model on `consent/route.ts`)

- `POST .../api/consent/grant` and `POST .../api/consent/revoke` (or a single route with
  `event_type` in body). Validate `category` (+ `rendering_class` required for
  `synthesized_voice`), `context`. SSR client, `auth.getUser()`; the row's `member_user_id` is
  set to `user.id` server-side (never from the body) so RLS member-only INSERT holds.
- A read endpoint/loader for current state (member: own; commissioner: members in their league)
  consuming the view.

### 5. Member consent surface (Member Office)

- A per-member consent panel in the Member Office (home: the Member Office page, `f0a40ed`),
  reusing the plain-language copy register of `src/components/founding/consent-panel.tsx`
  (NOT legalese). Shows the member's own current state per category, their own full event
  history, one-tap grant/revoke (W.6 section 5).
- Capture moments (L.1/L.3/L.4 flows) present only the categories that flow needs and link to
  the full panel - those are later units; this unit builds the canonical panel they link to.

### 6. Commissioner read-only

- Per-member current state, READ-ONLY, surfaced where uses are ratified (Office review, future
  W.1 tag ratification). The commissioner never edits consent and is NEVER shown aggregate
  consent stats (W.6 1.5 - consent state is never telemetry).

### 7. Tests (governance-test style, the G-series posture)

- RLS: a member can INSERT only their own events; a commissioner/admin CANNOT INSERT for a
  member (the W.6 1.3 governance test - mirror the approval_events `actor_user_id = auth.uid()`
  test); no UPDATE/DELETE succeeds for anyone (append-only).
- SELECT isolation: member A cannot read member B's consent rows; commissioner can read members
  in their own league only.
- Derived read: latest-event-wins; GRANT->REVOKE->GRANT resolves to GRANT; absence = no row =
  ungranted.
- 2e constraint: `synthesized_voice` requires `rendering_class`; others reject a non-null class.

## Binding constraints (from ratified W.6 - non-negotiable)

- Default-no-use: absence of a current GRANT = no capture/derivation/publication (1.4).
- Member-only authorship of GRANT and REVOKE; no commissioner/admin proxy (1.3).
- Append-only; current state is derived, never stored mutable (1.1).
- Never telemetry: no aggregate consent reporting, no completion nudges, no reminder cadences,
  no opt-in funnels (1.5, 8.1).
- Five independent categories, no bundles; 2e per-rendering-class, default opt-out (D-S, 2e).

## Acceptance criteria (binary)

1. `010_member_consent_events.sql` applies cleanly; table + view exist; RLS enabled.
2. RLS proven: member-only INSERT; no UPDATE/DELETE for anyone; cross-member SELECT denied;
   commissioner SELECT scoped to own league. (Tests in deliverable 7 pass.)
3. Member can grant/revoke each of the five categories (2e with a rendering_class) via the
   surface; their event history renders; current state reflects latest event.
4. Absence of any event for (member, category) reads as ungranted everywhere it is consumed.
5. Commissioner view is read-only and shows no aggregate counts.
6. `member_consent_events` + view registered in the Database allow-list; DB-shape guard green.
7. Existing suite green; no `founding_sessions.consent` write path changed (D-X: that field is
   reinterpreted, not migrated - leave it untouched).

## Gates (frontend repo discipline)

- Lint/typecheck/test per the frontend repo's own scripts (it has no engine-style prove_ci;
  use its package.json scripts + any governance test suite). Confirm on a clean tree.

## OUT OF SCOPE

- The `founding_sessions.consent` field: NOT migrated, NOT extended (D-X - reinterpret as
  league-defaults only). A separate frontend doc-note records the reinterpretation (W.6 7.1).
- Engine allowlist consumption / verifier wiring (W.6 7.3) - separate engine unit.
- The display-withdrawal UI (table may be created; UI deferred until published artifacts exist).
- Multi-league / cross-league consent semantics.
- Any synthesis rendering class (2e admits none; a future SAT class + per-class grant required).
- L.1/L.3/L.4 capture-moment flows (later units that link to this panel).

## Open decisions for the implementing session (none constitutional)

- Single grant/revoke route vs two routes.
- View `security_invoker` vs SECURITY INVOKER function (depends on Supabase PG version).
- Whether the display-withdrawal table ships in `010` or a `011` fast-follow.

---

Author's note (engine session, not part of the build brief): produced as Opus EXECUTE-prep
because W.6 pre-decided the design; grounded in reads of the frontend repo at `4e44bb3`. The
SAT-admission and build-routing flags are now RESOLVED by the founder (2026-06-10): build
straight, Opus, frontend repo - see Routing above. Cross-league consent semantics remains a
future question (out of scope). Target repo standardized on `~/squadvault` after a duplicate
clone was removed.
