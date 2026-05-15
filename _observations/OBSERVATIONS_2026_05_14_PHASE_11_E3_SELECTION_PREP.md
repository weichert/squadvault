# Phase 11 E3 (Commissioner Review-and-Approve UX) -- Selection-Prep

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map.
First memo in the E3 chain (selection-prep -> decision-readiness -> specification ->
registration IF E3 elects the Phase 11 route; or selection-prep -> Phase B arc IF it
elects the Phase B route). This is the only Phase 11 selection-prep whose chain may
terminate here by design.
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`.

**HEAD at authoring:** `83201d9` (Documentation Map v1.7).

**Predecessors (chain order, most-proximate last):**

- `bb0f325` -- Reset Memo v1.0 (doctrinal source)
- `ac96447` -- Documentation Map v1.6 (registry; v1.7 at `83201d9` is the current index)
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` -- Phase 11 surface-selection memo (E-cluster admissibility source; parent)
- `ba8b58a` -- Phase 11 Surface Roadmap (E3 admissibility section 2.2; Phase B escape
  hatch explicitly flagged: "Operational judgment whether to spec E3 as a registered
  Phase 11 surface or to ship as Phase B operational tooling")
- `9093a07` -- E1 specification (E-cluster first surface; review/approve lifecycle owner)
- `fa57056` -- E2-light specification (E-cluster second surface; chain pattern precedent)
- `993e97f` -- E2-light initial archive generation (E2-light operationally complete)
- `83201d9` -- Documentation Map v1.7 (current Map; E3 listed under Provisional Artifacts)

**Output:** E3's founding gate question -- Phase 11 registered surface or Phase B
operational tooling -- is adjudicated. Both paths are analyzed. A leading hypothesis
is registered. The chain's next step is founder-elected: if Phase B, this memo closes
the E3 chain and tasks E3 to the Phase B operational arc; if Phase 11, this memo opens
the decision-readiness chain as in prior surface selections.

---

## 1. Chain-step framing and the gate question

The Roadmap at `ba8b58a` section 2.2 registers E3 as admissible, with an explicit
routing question that no other Phase 11 surface has carried:

> "Commissioner-facing review-and-approve UX beyond CLI. Admissible per parent section 4
> E-cluster (light by construction; commissioner-only). Lower learning value than A or F
> surfaces; could ship as quality-of-life work during operational Phase B without needing
> a full Phase 11 surface selection cycle. **Operational judgment whether to spec E3 as a
> registered Phase 11 surface or to ship as Phase B operational tooling.**"

This routing question is the selection-prep's primary adjudication. Unlike A1/A2/A3/
E2-light (where the selection-prep opened a diagnostic arc leading directly to
decision-readiness), E3's selection-prep must first settle whether the full four-memo
Phase 11 chain is the right governance model for what E3 is.

**Two paths:**

- **Path P11:** E3 is specified as a registered Phase 11 product surface, goes through
  the full four-memo chain (decision-readiness Step 1 + Step 2 + specification), and
  lands a per-surface constitutional memo bound by template v1.0.
- **Path B:** E3 routes to the Phase B operational tooling arc, ships as an improved
  CLI/UX wrapper on the existing approval lifecycle (analogous to how Track A scripts
  shipped as operational tooling without Phase 11 surface specification overhead), and
  does not occupy a Phase 11 surface slot.

**The gate is a founder judgment under section 9.2.** This memo provides the analysis;
the founder elects.

---

## 2. Section-content load-bearing flags

Per E1 spec section 2 / A1-A3 chain carry-forward: doctrinal section-substance is
source-anchored in the predecessor chain. No fresh section-claim. Carry-forward applies.

**Confidence: medium-high.**

---

## 3. E3 identity carry-forward

Per Roadmap section 2.2 and parent memo `5a865a1` section 4 E-cluster screening:

**E3 -- Commissioner-facing review-and-approve UX beyond CLI.** Commissioner-only.
Light by construction. The current review/approve workflow is CLI-only:
`./scripts/py src/squadvault/consumers/editorial_review_week.py` to review a draft,
`./scripts/py src/squadvault/consumers/recap_week_approve.py` to approve it. E3 is
whatever makes that workflow more ergonomic -- a richer output format, an interactive
prompt, a formatted summary of the verification status alongside the recap text, a
withhold/approve choice in one pass.

**What E3 is not:**
- Not a league-member-facing surface. The commissioner is E3's direct user.
- Not a web application. Light shape means no hosting, no server, no auth.
- Not a new content class or artifact type. E3 wraps the existing approval lifecycle.
- Not E1 (which distributes approved recaps to the league) or E2-light (which archives
  them for readers).

---

## 4. Path P11 analysis -- E3 as a registered Phase 11 surface

**Arguments for P11:**

- E3 is listed as admissible in the Roadmap. The Roadmap's listing creates a default
  presumption of Phase 11 treatment unless the founder elects otherwise.
- A registered per-surface constitutional memo provides a formal spec for what the
  review UX should and should not do, which may be valuable as the project scales or
  onboards a second operator.
- Template v1.0 is now at `docs/templates/`; the overhead of authoring a spec is lower
  than before the template existed.

**Arguments against P11:**

- **Artisan-frame test (section 9.2):** The artisan-frame primary success criterion
  asks whether a surface delivers the "I had no idea" discovery moments for PFL Buddies
  members. E3's direct beneficiary is the commissioner, not the league members. E3 makes
  the commissioner's workflow more pleasant; it does not add to what league members
  experience or discover. This is a weak artisan-frame fit -- the weakest of any surface
  in the Phase 11 set.
- **No-New-Foundations risk:** A meaningful UX improvement beyond the current CLI
  (e.g., a TUI using `rich` / `textual`, or a local web review page) may require a new
  dependency or a small new infrastructure layer. Phase B operational tooling can absorb
  this more naturally than a Phase 11 surface spec.
- **Proportionality:** The four-memo constitutional specification chain is calibrated for
  league-product surfaces (what members see and interact with). Applying it to an
  internal commissioner tool is administratively heavy relative to the tool's scope.
- **Phase B is the right home:** Operational Plan section 8 Phase B (Track B: operational
  tooling, scheduler wiring, weekly digest) is explicitly the track for commissioner-side
  operational improvements. E3 is that kind of improvement.

**P11 verdict:** The artisan-frame test is the decisive factor. No other Phase 11 surface
has failed it; E3 is the first candidate that is genuinely commissioner-facing rather
than league-member-facing. The four-memo chain exists for league product surfaces. E3 is
not that.

---

## 5. Path B analysis -- E3 as Phase B operational tooling

**What Phase B tooling means for E3:**

A small improvement to the review/approve workflow, shipped in 1-2 commits as an
enhanced CLI script or a new combined `scripts/review_and_approve_recap.py` script.
Concrete shape options:

- **Option B1 (enhanced review output):** An updated `editorial_review_week.py` output
  that renders the recap text inline with verification status, week metadata, and a
  formatted summary -- using the Python stdlib or `rich` if already a dependency -- so
  the commissioner reads the full context before approving.
- **Option B2 (combined review-and-approve script):** A new `scripts/review_recap.py`
  that shows the formatted recap + verification status + prompts "Approve / Withhold /
  Skip" in one interactive pass, replacing the current two-step CLI workflow.
- **Option B3 (no change):** The current CLI is adequate; E3 ships as a documentation
  improvement (a runbook section) rather than new code.

**Phase B path does NOT:**
- Produce a per-surface constitutional memo.
- Occupy a Phase 11 surface slot.
- Go through the four-memo decision-readiness chain.
- Register in the Documentation Map as a commissioned Phase 11 surface.

**Phase B path DOES:**
- Ship a quality-of-life improvement to the commissioner's operational workflow.
- File a brief operational memo recording what shipped and why (analogous to the
  Track A distribution memos at `2f7d583` / `6537ef7` / `e15ddf8`).
- Close E3's Phase 11 chain at the selection-prep; the admissible-set updates to
  reflect E3 as "routed to Phase B" rather than "pending Phase 11 selection."

---

## 6. Leading hypothesis: Path B

**Leading hypothesis: E3 routes to Phase B operational tooling (Option B2 -- combined
review-and-approve script).**

The artisan-frame test is decisive: E3's direct beneficiary is the commissioner, not
league members. No Phase 11 surface has a weaker artisan-frame fit. Phase B is the
constitutionally-appropriate home for operational commissioner tooling. The proportionality
argument reinforces: the four-memo chain is calibrated for league-product surfaces; E3
is not that.

Option B2 (combined review-and-approve script) is preferred over B1 (enhanced output
only) because the current two-step workflow (separate review and approve commands) is the
actual friction point, and B2 addresses it directly. Option B3 (no code change) is
viable if probing the current workflow confirms the CLI is adequate.

**Confidence on leading hypothesis: medium-high.** The artisan-frame argument is strong.
The founder may legitimately elect P11 on the grounds that a formal spec for the review
UX is valuable for long-term governance or contributor onboarding -- a defensible
alternative that does not make the P11 election wrong.

---

## 7. Diagnostics (conditional on P11 election)

If the founder elects Path P11, the following diagnostics are registered for
decision-readiness Step 1 probes. If Path B is elected, these diagnostics are not needed.

**D1 -- Current review/approve workflow UX assessment.** Probe `editorial_review_week.py`
and `recap_week_approve.py` output formats. Is the current two-step workflow's friction
significant enough to warrant a structured E3 UX investment? What specific pain points
does the commissioner experience in practice?

**D2 -- Product-shape candidates.** TUI (rich/textual), local web review page, enhanced
CLI, combined interactive script. Which shape fits No-New-Foundations and is proportionate
to the commissioner's actual needs?

**D3 -- Data authority.** E3 reads `recap_artifacts` (draft text, verification results)
and writes to it (approve/withhold state transitions). Unlike all prior surfaces which
were read-only against the database, E3 is an operational tool that makes canonical
state changes. This is not a D3 violation -- the approval step is the correct write
event -- but it is architecturally distinct from the read-only presentation surfaces
(A1/A2/A3/E2-light). The spec must handle this explicitly.

**D4 -- Access mechanism.** Local-only, commissioner-only, no auth (per light-shape
constraint). CLI invocation pattern matches existing consumers.

**D5 -- Phase 11 vs Phase B (already adjudicated at this selection-prep).** Discharged
by founder election at this step.

---

## 8. The decision point

This selection-prep surfaces two options and a leading hypothesis. The founder elects:

**If Path B (leading hypothesis):**
- This memo closes the E3 Phase 11 chain.
- E3 is tasked to the Phase B operational arc: a combined review-and-approve script
  (Option B2) authored and committed as a Phase B operational improvement.
- The Phase 11 admissible-set updates: E3 is "routed to Phase B" (not pending Phase 11).
- A brief operational memo records what shipped and why.
- No per-surface constitutional memo. No template v1.0 exercise.

**If Path P11 (alternative):**
- Decision-readiness Step 1 is next: probes D1-D4 above.
- The chain proceeds through the full four-memo pattern.
- Template v1.0 at `docs/templates/` binds the spec session.
- E3 becomes the fourth post-ratification exercise of template v1.0.

---

## 9. Cluster / sequencing carry-forward

**E-cluster after E3 election:**
- If Path B: E-cluster is exhausted for Phase 11 purposes (E1 + E2-light shipped;
  E3 routed to Phase B). The admissible set reduces to F1 (substrate-contingent).
- If Path P11: E3 is in-chain; E-cluster Phase 11 exhausted upon E3 registration.

**F1 (Rivalry Chronicle):** Admissible contingent on substrate-readiness; unaffected
by E3's routing election.

**Roadmap admissible-surface-set after this selection-prep:**
- Shipped: E1, A1, A2, A3, E2-light.
- In-chain: E3 (this memo; routing election pending).
- Admissible, contingent on substrate-readiness: F1.

---

## 10. Prior-attempt findings

No prior failed attempt at an E3 brief.

**Confidence: high.**

---

## 11. Confidence labeling

### 11.1 Highest-confidence claims

- **The gate question is real and must be adjudicated.** The Roadmap explicitly names it;
  it is not a formality. (section 1)
- **The artisan-frame test is the decisive factor.** E3's direct beneficiary is the
  commissioner, not league members; this is a structural fact, not a judgment call.
  (section 4)
- **Path B is the cleaner constitutional home for E3.** Phase B is explicitly the track
  for operational commissioner tooling. (section 5)

### 11.2 Medium-high confidence claims

- **Option B2 (combined review-and-approve) is the right Phase B shape.** The two-step
  CLI friction is the actual pain point; B2 addresses it directly.
- **The founder may legitimately elect P11.** The formal-spec-for-governance argument is
  real; P11 is not wrong, just heavier than the task warrants.

### 11.3 Claims this memo deliberately does not make

- No characterization of the current CLI's specific UX pain points. That is a D1 probe.
- No commitment on which Python library (rich, textual, curses) E3 uses.
- No pre-authoring of the Phase B operational memo.
- No pre-determination of the E-cluster exhaustion outcome (that depends on E3's routing
  election).

---

## 12. Cross-references

- `bb0f325` -- Reset Memo v1.0
- `1cf4142` -- Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` -- Phase 11 surface-selection memo (E-cluster admissibility source)
- `ba8b58a` -- Phase 11 Surface Roadmap (E3 section 2.2; Phase B escape hatch)
- `9093a07` -- E1 specification (review/approve lifecycle owner; approval consumer chain)
- `fa57056` -- E2-light specification (E-cluster second surface; chain pattern precedent)
- `83201d9` -- Documentation Map v1.7 (current Map; E3 in Provisional Artifacts)
- `src/squadvault/consumers/editorial_review_week.py` -- current review consumer (D1)
- `src/squadvault/consumers/recap_week_approve.py` -- current approve consumer (D1)
- `SquadVault_Operational_Plan_v1_1.md` section 8 -- Phase B operational track

---

**Filing:** `_observations/OBSERVATIONS_2026_05_14_PHASE_11_E3_SELECTION_PREP.md`.
Provisional / observational. No tier. No Map registration.

**Decision point:** Founder elects Path B (Phase B tooling -- chain closes here, E3
routes to Phase B operational arc) or Path P11 (Phase 11 surface -- decision-readiness
Step 1 is next). Leading hypothesis: Path B.
