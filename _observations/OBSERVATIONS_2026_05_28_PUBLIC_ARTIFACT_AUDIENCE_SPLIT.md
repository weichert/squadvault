# OBSERVATIONS — Public Artifact Audience Split (2026-05-28)

**Surfaced by:** Milestone 3 Track B spot-check against the live archive.
**Engine HEAD at observation:** `c9dcf11` (or whatever the synced HEAD recorded in `sync_log` resolves to).
**Frontend HEAD at observation:** `ad644bd` + Track B archive surfaces (uncommitted at memo-author time).
**Disposition:** Observation only. No architectural change this milestone. Surfacing choice deferred to a follow-on session.
**Append-only:** This memo records the finding. It does not edit any prior memo, schema, or artifact.

---

## 1. Observation

The first visual spot-check of `/league/70985/archive/recaps/<id>` against a synced 2025 weekly recap (`SV-2025-W13-V23`, engine id 1259) revealed that the `rendered_text` field of a `WEEKLY_RECAP` artifact contains **two audience segments concatenated into one string**, separated by literal delimiter lines:

```
--- SHAREABLE RECAP ---
[league-facing prose]
--- END SHAREABLE RECAP ---
```

Above the delimiter: a commissioner-grade audit trail — window timestamps, selection fingerprint, event-class breakdown, full trace IDs, the "summary-only / no fabrication" self-declaration, and the bulleted enumeration of source events (waiver awards, free-agent moves) that the narrative is allowed to reference.

Below the delimiter: a richly-voiced league-facing recap — score callouts with bench-misplay observations, FAAB pricing context, playoff-implication framing.

Both segments are valid records by the engine's principles. They serve different readers.

The W18-2025 degenerate case (`SV-2025-W18-V15`, the platform-duplicate week) confirms the structure is intentional: when the shareable segment cannot be honestly produced, the engine emits only the audit trail plus its own "Creative narrative skipped — silence over fabrication" note, and *no* `--- SHAREABLE RECAP ---` delimiter pair appears. The delimiter is a present-when-needed boundary, not a fixed schema field.

## 2. What the archive surface currently does

The Milestone 3 Track B `recaps/[artifactId]/page.tsx` renders `artifact_versions.content_markdown` verbatim through `<ReactMarkdown>`. Anonymous archive readers see the union: audit trail plus shareable segment (when present), bracketed by the CERTIFIED trust bar.

This is **not wrong by governance principles** — it is the strongest possible transparency posture. Every league member can see exactly what the commissioner saw, including the engine's self-declared restraint. The fabrication-resistance is *visible* on the public surface.

But it is a surfacing decision that was inherited by the Milestone 3 default-render path, not chosen explicitly. The decision deserves to be made deliberately.

## 3. Three options

### Option A — Render the union (current state)

Maximum transparency. The audit trail *is* part of the record because it proves the narrative wasn't fabricated. Members who want only the prose scroll past the trace header. Zero code change.

**Trade-off:** the public-facing reading experience has friction. The first ~10 lines of every recap are timestamps, hashes, and trace IDs that mean nothing to a league member.

### Option B — Render-time split at the delimiter

Frontend splits `content_markdown` on `--- SHAREABLE RECAP ---` at render time. Public archive surfaces show the segment between the delimiters; commissioner-facing surfaces (the existing approve/review route) continue to show the union.

Falls back gracefully on segment-absent recaps (W18-style silence cases) — the whole string is rendered as one segment, which displays the audit trail and the "silence over fabrication" note, which *is* the correct league-facing message for those weeks.

**Trade-off:** the public surface no longer carries the visible fabrication-resistance proof. The audit trail remains immutable and accessible to the commissioner; members trust the trust bar plus their commissioner's vouching.

**Implementation cost:** ~15 lines in `recaps/[artifactId]/page.tsx`. `rendered_text` is not modified. The split is a presentation choice, not a fact mutation.

### Option C — Generation-time split into separate artifacts (or structured payload)

Engine emits two `rendered_text` fields, two `recap_artifacts` rows per week, or one row with a structured payload field carrying the two segments separately.

**Trade-off:** architectural. Touches the engine, the schema, the sync script, and the renderer. Wrong scope for this milestone. Worth filing as a Phase-12-or-later spec candidate if Option B proves insufficient.

## 4. Recommendation

**Option B,** with the audit trail remaining unconditionally visible on the commissioner approval/review surface (which already exists at `/league/[id]/approve/[artifactId]`).

Rationale: the audit trail's audience *is* the commissioner. The shareable segment's audience *is* the league. The engine has already done the audience separation in `rendered_text` via the delimiter; the front end should honor it. Members trust the CERTIFIED trust bar plus the commissioner-vouches-by-approving chain; they do not need to read raw trace IDs to receive that trust.

The "fabrication-resistance is visible on the public surface" argument for Option A is real but second-order: the same resistance is *demonstrated by what's in the prose* (deterministic scores, named events, no invented quotes) and *guaranteed by the governance chain* (engine selection layer + commissioner approval), not only by displaying the trace header.

**Disposition:** Recommendation recorded; decision deferred. Not blocking Milestone 3 close. Open as a follow-on once the full archive surface has been lived with for at least one approval cycle of new content.

## 5. Related observation — F1 packed `week_index`

Same shape of seam, different surface:

Track A's full sync produced four F1 (RIVALRY_CHRONICLE_V1) rows with `week_index = 204510` and dockets like `SV-2025-W204510-CHRONICLE-V03`. Inspection of `persist_rivalry_chronicle_v1.py` indicates the engine's chronicle persistence encodes a multi-week anchor (likely weeks 4 / 5 / 10 or similar tuple) into a packed integer for storage, and uses the `version` column as a discriminator across team-pair rivalries that share the same anchor.

The Supabase rows are *structurally correct* (each rivalry is its own UUID-keyed artifact with its own content), but the docket text `SV-2025-W204510-CHRONICLE-V03` is not human-meaningful. The packed value has not been decoded on the frontend, and F1 has no archive surface this milestone (deferred per Milestone 3 brief section 7), so the cosmetic shortfall is unrendered.

This is the same architectural seam as section 1: the engine emits a value that requires interpretation; the frontend either renders the engine's encoding raw, or decodes at render time, or asks the engine to emit a decoded form. The section 3 options above translate one-for-one to F1's case.

**Disposition:** Recorded for the F1 archive-surface milestone, whenever that lands.

## 6. Cross-references

- **Milestone 3 brief** section 3 (sync semantics) — defines the engine artifact source as `recap_artifacts.rendered_text`; does not constrain how the frontend renders the field.
- **Milestone 3 brief** section 7 — F1 archive surface deferred.
- **Milestone 3 brief** section 8 — Design Brief established trust bar as "part of the artifact, not floating"; this memo does not disturb that.
- **Reset Memo v1.0** section 2.3 — "silence over speculation" doctrine; W18-2025 engine self-note (`Creative narrative skipped — silence over fabrication`) is this doctrine literally visible.
- **`scripts/sync_to_supabase.py`** (Milestone 3 Track A) — the sync surfaced this observation by making the artifacts publicly readable; the script itself is unaffected by the disposition.

## 7. Append-only

This memo records an observation about how `rendered_text` is structured and how the Milestone 3 Track B surface renders it. It does not modify any artifact, schema, RLS policy, or generation path. The recommendation in section 4 is recorded for future deliberation; no code change accompanies this memo.
