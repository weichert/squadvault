# Option B scoping — nickname override layer

**Date:** 2026-04-22
**Scope:** Scoping only. No `src/` or `Tests/` changes, no DB mutations,
no ingest runs, no MFL probes. Enumerates the design space across four
axes (schema, code, regression tests, auth-plumbing boundary) and
selects a specific implementation path for the session that follows.
**HEAD at observation-time:** `3e4dabc` — Phase 10 observation:
owner-name step 5 + Option B decision.
**Follows:** `3e4dabc` — 04-19 decision memo, which mechanically
selected Option B via the pre-read's decision rule against force-auth
MFL probe evidence (0002/KP Shape B).

---

## SHA-256 drift check

State captured at session open:

| File | SHA-256 | Brief match |
|---|---|---|
| `src/squadvault/core/recaps/verification/recap_verifier_v1.py` | `745d1f8ad9dfadd0c5c2cb935611839b0ca1d20e00b89c922aff27190e9f8752` | ✅ |
| `src/squadvault/ingest/franchises/_run_franchises_ingest.py` | `0b1ea91a47c37cbbe6b83915bfed19d3bd5a6b9da50c2973f866d51fc562c70f` | ✅ |
| `src/squadvault/mfl/client.py` | `1ea40f247a1fbe4eac3370a69367e3bd5e46fd4ceefed10ecbb55667f985142d` | ✅ |
| `src/squadvault/mfl/historical_ingest.py` | `4210016b5095985e7661320db4edc7aae768d1fedbaf824232e3bf0d5773e843` | ✅ |
| `src/squadvault/mfl/discovery.py` | `e25f4c2bda6b67ffbdb1f76836e0415d8f48c1ae3475442c684b6a13350465ed` | first-pin (brought into scope by 04-19 incidental finding) |

No drift. Findings below are grounded in the committed HEAD.

---

## Design-axis summary

**Schema axis (Q1–Q4):** where does league-used nickname data live?
Three candidates: a new column on `franchise_directory` (per-season,
piggybacks on existing ingest lifecycle), a separate cross-season
table `franchise_nicknames` keyed by `(league_id, franchise_id)`, or
a git-versioned config file. Nicknames are stable identity markers
that do not change per-season, which argues against per-season
storage. None of the three options breaks append-only discipline
when paired with the correct write governance. The adapter-contract
check is satisfied trivially — nickname is additive to the MFL
adapter's output, not a replacement, because MFL has no nickname
field to disconnect from in the first place.

**Code axis (Q5–Q8):** how does `_build_reverse_name_map` consume
nickname data? Three candidates: a new pass 5 after owner-first-word
extraction, a pass-4 override that prefers nicknames, or
pre-pass-4 injection that uses pass 4's existing non-override guard
(`recap_verifier_v1.py:409`) to establish nickname preference by
construction. Pre-pass-4 injection requires the minimum code change
because the existing guard at line 409 already does the right thing
when nickname aliases are present before pass 4 runs. The separate
loader question (Q8) is straightforward: a new
`_load_franchise_nicknames` alongside the existing
`_load_franchise_owner_names` preserves separation of concerns
(curation-sourced vs MFL-sourced) and leaves
`_load_franchise_owner_names`'s contract untouched.

**Regression test axis (Q9–Q11):** minimum viable fixture set covers
the Shape B dead-alias resolution (the load-bearing case for KP),
Shape A no-regression (ensures pass 4's existing owner-first-word
extraction still works for Pat/Steve/Michele), nickname-absent
fallback (validates the cold-start state where no curation has been
performed does not regress today's behavior), and theoretical
nickname collision suppression. All four belong at the
`_build_reverse_name_map` unit level adjacent to the existing test
at `Tests/test_recap_verifier_v1.py:258-262`. Backward compatibility
with the live-DB-mirror test at line 2462 is preserved by making
`nickname_map` default to `None` (same pattern as today's `owner_map`).

**Auth-plumbing boundary axis (Q12–Q14):** does Option B require
re-ingesting `owner_name` — and therefore Option (ii) as a
precondition — or is nickname purely additive? Empirical grounding:
the only `src/` consumer of `franchise_directory.owner_name` is
`_load_franchise_owner_names`, which feeds only the pass-4 alias
derivation. No other reader exists. If the nickname layer supersedes
pass-4 alias derivation for the four critical franchises, then
owner_name becomes a zero-consumer column whose population status is
observationally irrelevant. This is the decisive evidence for
branch (a): nickname-only, owner_name-population deferred
indefinitely, Option (ii) fully independent and not a precondition.

---

## Schema axis — options enumeration

### Q1 — Where does nickname data live?

#### Option S1 — New column `owner_nickname` on `franchise_directory`

DDL sketch (next migration would be `0010_add_owner_nickname.sql`):

```sql
ALTER TABLE franchise_directory ADD COLUMN owner_nickname TEXT;
```

**Pros:**
- Minimum schema change. One column, no new table.
- Discoverable via `.schema franchise_directory`.
- Co-located with existing franchise identity fields.

**Cons:**
- **Per-season duplication.** `franchise_directory` is keyed
  `(league_id, season, franchise_id)`. A nickname that is stable
  across all 17 seasons would require 17 identical writes per
  franchise. That's 170 rows for this league to carry 10 stable
  facts.
- **Write governance ambiguous.** `_run_franchises_ingest.py:162`
  UPSERTS `owner_name` from MFL on every re-ingest. If
  `owner_nickname` lives in the same table, the question "does ingest
  touch this column?" must be answered. If no, then ingest's UPSERT
  clause must explicitly exclude it (additional code to maintain
  separation). If yes, then ingest becomes the writer (but MFL has no
  nickname field, so what would it write?).
- **Not cross-season by natural key.** The PK is
  `(league_id, season, franchise_id)`. Querying "what is franchise
  0002's nickname" requires `WHERE season = ?` — but the answer
  should not depend on the season.

#### Option S2 — New table `franchise_nicknames`

DDL sketch (next migration would be `0010_add_franchise_nicknames.sql`):

```sql
CREATE TABLE IF NOT EXISTS franchise_nicknames (
  league_id      TEXT NOT NULL,
  franchise_id   TEXT NOT NULL,
  nickname       TEXT NOT NULL,
  curated_by     TEXT NOT NULL DEFAULT 'commissioner',
  curated_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY (league_id, franchise_id)
);
```

**Pros:**
- **Cross-season natural key** — `(league_id, franchise_id)`,
  no `season` column. One row per franchise per league, 10 rows total
  for PFL Buddies. Matches the semantic shape of the data.
- **Precedent exists.** `league_voice_profiles` (schema.sql:328-346,
  migration 0006) follows the same pattern — cross-league config,
  commissioner-curated, `(league_id)` primary key, `curated_by` +
  `curated_at` provenance columns. `league_tone_profiles` (migration
  0004) is similar.
- **Write governance explicit.** Ingest does not write this table.
  The separation is structural, not by convention.
- **Append-only compatible.** Same pattern as voice profiles — a
  row exists once per (league, franchise) and updates are explicit
  commissioner actions, auditable via `curated_at`.
- **SQL-diagnosable.** `sqlite3 … "SELECT * FROM franchise_nicknames
  WHERE league_id='70985'"` returns 10 rows during verification.

**Cons:**
- One more table in the schema.
- New loader required (but Q8 concludes a separate loader is
  preferred regardless).

#### Option S3 — Git-versioned config file

File layout sketch:

```toml
# config/franchise_nicknames.toml
[league."70985".franchises]
"0002" = "KP"
"0003" = "Pat"
"0005" = "Steve"
"0009" = "Michele"
```

**Pros:**
- **Git-versioned by construction** — changes are diffable, reviewable,
  auditable via `git log`. Strongest append-only story.
- No DB write path, therefore no auth-plumbing question at all.
  Fully orthogonal to Option (ii).
- Operator edits with normal tooling (editor, git commit).

**Cons:**
- **New file-loading codepath.** This repo currently has no
  TOML/YAML config loader. `configparser` for INI exists in stdlib
  but the convention here is SQL-backed. Introducing a config-file
  mechanic just for nicknames is a precedent-setting decision.
- **Environment-specific availability.** The config file must be
  present in every execution environment. `franchise_directory`
  already travels with the DB; a config file requires separate
  distribution.
- **Not SQL-diagnosable.** Verification scripts that inspect the DB
  cannot see nicknames without a parallel file-reading path.
- No precedent in this codebase for league-specific TOML/YAML config
  files. The closest analogue (`league_voice_profiles`) lives in
  the DB.

### Q2 — Per-season or cross-season semantics?

Cross-season. The four critical franchises (0002/KP, 0003/Pat,
0005/Steve, 0009/Cavallini) have carried the same league-used
short-forms across multiple seasons. The 04-19 decision memo's
17-season inventory (2009–2025, `n_name_populated = 10` across all)
shows franchise identity is stable across the league's MFL history.
Nicknames follow that stability.

This argues against S1 (per-season column) and in favor of S2 or S3,
which key on `(league_id, franchise_id)` without `season`.

### Q3 — Append-only discipline check

| Option | Append-only story |
|---|---|
| S1 (column) | Weakest. Per-season rows UPSERTed by ingest (`_run_franchises_ingest.py:162`). `owner_nickname` would either piggyback on ingest's UPSERT semantics (and what populates it?) or require explicit exclusion. |
| S2 (table) | Strong. Mirrors `league_voice_profiles`. `curated_at` column provides provenance. Writes are explicit commissioner actions, not ingest side-effects. |
| S3 (config) | Strongest. `git log` is the history. No mutation outside diff-able file edits. |

### Q4 — Adapter-contract check (Platform Adapter Contract Card)

The adapter contract's relevant requirement (04-21 pre-read, Option C
discussion) is that we should not "disconnect `owner_name` from
MFL" — i.e., the MFL-sourced field should remain MFL-sourced, not be
replaced by curation.

None of S1/S2/S3 violates this, because the nickname layer is
**additive**, not a replacement. MFL has no nickname concept — there
is nothing to disconnect. `owner_name` continues to reflect whatever
MFL returns; `nickname` is a separate, curation-only field that
SquadVault introduces without any MFL-side counterpart.

All three schema options pass the adapter-contract check.

### Schema recommendation

**Option S2 — new table `franchise_nicknames` keyed
`(league_id, franchise_id)`.**

Rationale (ranked by load-bearing weight):

1. **Cross-season natural key matches data shape.** Nicknames are
   stable identity markers. S1's per-season duplication is a data-
   shape mismatch.
2. **Precedent inside the codebase.** `league_voice_profiles`
   (schema.sql:328-346) establishes the pattern for commissioner-
   curated, cross-league tables. Option B fits that precedent
   without introducing a new convention.
3. **SQL-diagnosable.** Aligns with the existing diagnostic
   workflow (`sqlite3 .local_squadvault.sqlite …`) that underpins
   every observation memo in this project.
4. **Write governance structurally separated from ingest** without
   requiring ingest-side code changes.

S3 (config file) is the close runner-up and would be preferable if
append-only discipline were the dominant consideration in isolation.
It loses on codebase-precedent grounds (no TOML/YAML loader exists),
diagnostic accessibility (SQL tooling can't see it), and
environment-distribution (config must travel separately from the DB).
If future requirements surface operator-curation use cases that
benefit from git-diffable changes, revisiting S3 in a different
scoping pass is defensible — but this pass does not carry enough
evidence to prefer it now.

S1 (column on franchise_directory) is rejected on cross-season-key
mismatch and ingest write-governance ambiguity.

---

## Code axis — options enumeration

### Q5 — Where in `_build_reverse_name_map` does nickname consumption happen?

Current pass structure (`recap_verifier_v1.py:314-412`):

- Pass 1 (314-320): full franchise names, case and lowercase.
- Pass 2 (322-348): first-word franchise-name aliases.
- Pass 3 (350-380): last-word franchise-name aliases.
- Pass 4 (381-410): owner first-word aliases, guarded by
  `if owner_map:` at line 388 and `if alias not in reverse:`
  non-override at line 409.

#### Option C1 — New pass 5 after pass 4

Runs after pass 4. Nickname-sourced alias overrides pass-4 owner-
first-word alias for the same franchise if both would produce aliases.

Code sketch:

```python
# Pass 5: Curated nickname aliases (when nickname_map supplied).
# Overrides pass-4 owner-first-word extraction for franchises where
# the league uses a short-form that differs from the owner's legal
# first name ("KP" vs "Kent", "Pat" vs "Patrick").
if nickname_map:
    _nickname_to_fids: dict[str, set[str]] = {}
    for fid, nickname in nickname_map.items():
        if fid not in name_map:
            continue
        alias = nickname.strip().lower()
        if len(alias) < 2:
            continue
        if alias in _stop_words:
            continue
        _nickname_to_fids.setdefault(alias, set()).add(fid)

    for alias, fids in _nickname_to_fids.items():
        if len(fids) != 1:
            continue
        fid = next(iter(fids))
        # Override semantics: nickname supersedes pass-4 owner-first-word
        # for the same franchise, but does NOT override passes 1-3
        # (franchise-name-derived aliases). Detect pass-4-sourced entries
        # by checking whether reverse[alias] currently points to a
        # franchise whose owner first-word would produce this alias.
        ...  # override rule needs explicit "was this alias from pass 4?" check
        reverse[alias] = fid
```

**Pros:**
- Clean separation from pass 4; preserves pass-4 behavior exactly.
- Explicit "this pass is curated nicknames" framing.

**Cons:**
- **Override rule requires tracking alias provenance.** Distinguishing
  "pass 4 put `kp` here" from "pass 2 put `kp` here" (hypothetical
  collision with a franchise name) is not cheap. Either introduce a
  parallel `reverse_source: dict[str, str]` map, or compute pass-4
  aliases a second time inside pass 5 to compare. Both are structural
  overhead for a case that does not exist in this league (Risk 3 cleared).
- Conceptually asks the reader to understand two mechanisms for
  "owner-derived alias preference" — unconditional (pass 5) and
  non-override (pass 4) — when the intent is simpler.

#### Option C2 — Pass-4 override

Modify pass 4 itself to prefer `nickname_map[fid]` over
`re.findall(r"\w+", owner)[0].lower()` when both are available.

Code sketch:

```python
# Pass 4: Owner-derived aliases. Prefers curated nickname when
# provided (handles shape-B dead-alias cases like KP/Kent), falls
# back to first-word of owner_name otherwise.
if owner_map or nickname_map:
    _owner_word_to_fids: dict[str, set[str]] = {}
    for fid in set((owner_map or {}).keys()) | set((nickname_map or {}).keys()):
        if fid not in name_map:
            continue
        if nickname_map and fid in nickname_map:
            candidate = nickname_map[fid].strip().lower()
        elif owner_map and fid in owner_map:
            normalized = _normalize_apostrophes(owner_map[fid])
            words = re.findall(r"\w+", normalized)
            if not words:
                continue
            candidate = words[0].lower()
        else:
            continue
        if len(candidate) < 2 or candidate in _stop_words:
            continue
        _owner_word_to_fids.setdefault(candidate, set()).add(fid)
    # ... collision-suppress and non-override as today
```

**Pros:**
- Single pass handles both data sources.
- Preference order enforced by per-franchise `if nickname_map and fid in nickname_map` branch.

**Cons:**
- **Conflates two distinct data sources in one pass.** Makes it
  harder to reason about the pass's invariants (what values can
  `candidate` hold? where did it come from? do they have the same
  normalization semantics?).
- **Changes the existing pass-4 signature and control flow.** Any
  future reader who has internalized "pass 4 = owner first-word"
  has to re-learn. The 04-19 decision memo's
  `recap_verifier_v1.py:388-410` reference becomes a trap.
- Diff is larger than C3.

#### Option C3 — Pre-pass-4 injection (recommended)

Insert a nickname pass **before** pass 4. Pass 4's existing
non-override guard at line 409 (`if alias not in reverse:`)
naturally skips any alias the nickname pass has already populated.

Code sketch:

```python
# Pass 4a: Curated nickname aliases (when nickname_map supplied).
# Runs before the owner first-word extraction below so that
# nicknames take precedence over pass-4b's extracted first-words
# via the existing non-override guard. Resolves shape-B dead-alias
# cases where the league uses a short-form ("KP") that differs
# from the owner's legal first name ("Kent").
if nickname_map:
    _nickname_to_fids: dict[str, set[str]] = {}
    for fid, nickname in nickname_map.items():
        if fid not in name_map:
            continue
        alias = nickname.strip().lower()
        if len(alias) < 2:
            continue
        if alias in _stop_words:
            continue
        _nickname_to_fids.setdefault(alias, set()).add(fid)

    for alias, fids in _nickname_to_fids.items():
        if len(fids) != 1:
            continue
        fid = next(iter(fids))
        if alias not in reverse:
            reverse[alias] = fid

# Pass 4b: Owner first-name aliases (when owner_map supplied).
# [UNCHANGED — existing lines 381-410]
if owner_map:
    _owner_word_to_fids: dict[str, set[str]] = {}
    ...
```

**Pros:**
- **Minimum code change.** Pass 4a is a near-copy of pass 4b with
  the data source swapped. Pass 4b is literally unchanged.
- **Correct preference order by construction.** The non-override
  guard at existing line 409 is the mechanism. No new "which pass
  put this here?" bookkeeping needed.
- **Natural naming.** Pass 4a (curated) + Pass 4b (extracted) makes
  the intent transparent: same broad category of "owner-derived
  aliases," two data sources, curation wins.
- **Smallest blast radius.** The only change to pass 4b is the
  docstring reference to its sibling; the body is untouched.

**Cons:**
- Pass renumbering (4 → 4a + 4b) affects the docstring and comments
  only, but any external reference to "pass 4" in documentation
  would need re-homing. Grep for references: none found in `src/`
  beyond the verifier file itself; the 04-19 and 04-21 memos refer
  to "pass 4" by line number (395-398, 406, 409), not pass number,
  so their references continue to resolve correctly.

### Q6 — Preference order when both sources produce a candidate alias

Specification (applies to C3):

- For franchise 0002 (KP): nickname "KP" produces alias `kp`.
  Owner first-word "Kent" produces alias `kent`. These are
  **different aliases for the same franchise**. Both are written
  into `reverse`: `reverse["kp"] = F_KP` from pass 4a,
  `reverse["kent"] = F_KP` from pass 4b. No conflict; both aliases
  route to 0002. Deferred-alias risk: if subsequent prose uses
  "kent," it resolves correctly even though the league does not
  typically use that form. Not a regression; an incidental
  benefit.

- For franchise 0005 (Steve): nickname "Steve" produces alias
  `steve`. Owner first-word "Steve" produces alias `steve`. Same
  alias. Pass 4a writes first; pass 4b's non-override guard at
  line 409 skips. Net effect: `reverse["steve"] = F_WEICHERT` from
  pass 4a. Functionally indistinguishable from pass 4b writing
  the same value.

- For franchise 0003 (Pat): nickname "Pat" produces alias `pat`.
  Owner first-word "Pat" produces alias `pat`. Same as Steve case.

- For franchise 0009 (Cavallini/Michele): nickname "Michele"
  produces alias `michele`. Owner first-word "Michele" produces
  `michele`. Same as Steve case.

Result: curation-first, extraction-fallback. No overrides needed;
the non-override guard does the work.

### Q7 — Collision suppression for the nickname pass

Same semantics as pass 4b (existing line 406): if two franchises
share a nickname, neither gets an alias. This is theoretical
robustness only — Risk 3 (04-19 decision memo) was cleared via
empirical check: all 10 pass-4b lowercased first-word aliases
are distinct for PFL Buddies 2025. Curated nicknames are set by
the commissioner and would not plausibly collide either, but the
guard is cheap and matches existing convention.

Recommendation: use the same `if len(fids) != 1: continue`
pattern as pass 4b.

### Q8 — Does `_load_franchise_owner_names` change, or is nickname a separate loader?

**Separate loader recommended.** Rationale:

1. **Preserves existing loader's contract** —
   `_load_franchise_owner_names` (line 174-198) returns `dict[str, str]`
   of non-empty owner names from `franchise_directory`. Its caller
   at line 2944 and `scripts/verify_season.py:112` continue to
   function identically.
2. **Separates concerns by data source.** MFL-sourced owner names
   flow through one loader; curation-sourced nicknames flow through
   another. Future readers can trace each data path independently.
3. **Independent failure modes.** If `franchise_nicknames` is empty
   or the table is missing (first-run-before-curation state), the
   nickname loader returns `{}`. The owner_map loader is unaffected.
4. **Matches precedent.** `_load_franchise_names` (line 154-171)
   and `_load_franchise_owner_names` (line 174-198) are already
   two separate loaders for two columns of the same table. Adding
   `_load_franchise_nicknames` follows the same pattern.

Loader signature (selected under Option S2):

```python
def _load_franchise_nicknames(
    db_path: str,
    league_id: str,
) -> dict[str, str]:
    """Load franchise_id -> nickname map (cross-season).

    Curated league-used short-forms for franchise owners. Returns
    only non-empty nicknames; missing rows silently omitted.
    """
    nickname_map: dict[str, str] = {}
    with DatabaseSession(db_path) as con:
        rows = con.execute(
            """SELECT franchise_id, nickname
               FROM franchise_nicknames
               WHERE league_id = ?""",
            (str(league_id),),
        ).fetchall()
    for row in rows:
        if row[0] and row[1] and str(row[1]).strip():
            nickname_map[str(row[0]).strip()] = str(row[1]).strip()
    return nickname_map
```

Note: no `season` parameter — matches Option S2's cross-season
natural key. Call site at line 2944 adds one line:

```python
owner_map = _load_franchise_owner_names(db_path, league_id, season)
nickname_map = _load_franchise_nicknames(db_path, league_id)
reverse_name_map = _build_reverse_name_map(name_map, owner_map, nickname_map)
```

`scripts/verify_season.py:112` — same one-line addition. If the
table is absent (transitional, pre-migration), the loader raises
`sqlite3.OperationalError`. Migration 0010 must run before the
first verify call. This is the same contract every migration-
backed table carries; no special handling.

### Code recommendation

**Option C3 — Pre-pass-4 injection, with pass renaming to 4a/4b.**
Separate loader `_load_franchise_nicknames` per Q8.

Rationale (ranked by load-bearing weight):

1. **Minimum code change to achieve the goal.** Pass 4a is a near-
   copy of existing pass 4b with the data source swapped. Pass 4b
   is structurally unchanged.
2. **Correct preference order by construction.** The existing
   non-override guard at line 409 is the mechanism. No alias-
   provenance tracking needed.
3. **Zero structural impact on passes 1–3.** Pass 1 (full names)
   and passes 2–3 (franchise-name-derived) run identically.
4. **Backward compatibility preserved.** Signature becomes
   `_build_reverse_name_map(name_map, owner_map=None, nickname_map=None)` —
   both new parameters default to `None`, matching today's `owner_map`
   pattern. Every existing call site continues to work without
   modification (Q11).

C1 (new pass 5) is rejected because it requires alias-provenance
tracking that does not justify its complexity for a case Risk 3
already cleared. C2 (pass-4 override) is rejected because it
conflates two data sources in a single pass, diverging from the
"one pass = one data source" structure that makes the current code
readable.

---

## Regression test axis — fixture plan (Q9–Q11)

### Q9 — Minimum viable fixtures

All four fixtures belong in a new test class
`TestBuildReverseNameMapNickname` in `Tests/test_recap_verifier_v1.py`,
adjacent to the existing owner-alias test at line 258-262. Each
fixture is one test method.

**Fixture N1 — Shape B dead-alias resolved (the load-bearing case)**

```python
def test_nickname_resolves_shape_b_dead_alias(self) -> None:
    """KP case: owner 'Kent Paradis' alone would produce 'kent' (dead);
    nickname 'KP' resolves correctly."""
    name_map = {"F_KP": "Paradis' Playmakers"}
    owner_map = {"F_KP": "Kent Paradis"}
    nickname_map = {"F_KP": "KP"}
    reverse = _build_reverse_name_map(name_map, owner_map, nickname_map)
    assert reverse.get("kp") == "F_KP"
    # Pass 4b still populates 'kent' from owner first-word (incidental benefit)
    assert reverse.get("kent") == "F_KP"
```

Assert targets: `reverse.get("kp") == "F_KP"` is the primary pin.
The `kent` assertion pins pass 4b's unchanged behavior alongside the
new pass 4a.

**Fixture N2 — Shape A no regression**

```python
def test_nickname_empty_preserves_pass_4b_extraction(self) -> None:
    """Pat case: nickname-map empty, owner first-word extraction
    still yields 'pat' from 'Pat Nocero'."""
    name_map = {"F_PAT": "Purple Haze"}
    owner_map = {"F_PAT": "Pat Nocero"}
    nickname_map: dict[str, str] = {}
    reverse = _build_reverse_name_map(name_map, owner_map, nickname_map)
    assert reverse.get("pat") == "F_PAT"
```

Assert targets: `reverse.get("pat") == "F_PAT"` pins that pass 4b is
not regressed by the introduction of pass 4a.

**Fixture N3 — Nickname absent under Shape B (cold-start state)**

```python
def test_nickname_missing_under_shape_b_stays_broken(self) -> None:
    """Validates cold-start state (pre-curation). Documents today's
    broken behavior is unchanged when nickname_map is empty."""
    name_map = {"F_KP": "Paradis' Playmakers"}
    owner_map = {"F_KP": "Kent Paradis"}
    nickname_map: dict[str, str] = {}
    reverse = _build_reverse_name_map(name_map, owner_map, nickname_map)
    # Pass 4b extracts 'kent' (dead-alias case from 04-19 memo)
    assert reverse.get("kent") == "F_KP"
    # 'kp' is NOT in the map because no nickname was provided
    assert "kp" not in reverse
```

Assert targets: `"kp" not in reverse` pins the pre-curation state.
Explicit guard against accidentally fabricating aliases from owner
data alone. This test will **pass today** (cold-start state is
current state) and **continue to pass** post-migration until the
commissioner curates `franchise_nicknames`.

**Fixture N4 — Nickname collision suppression**

```python
def test_nickname_collision_suppressed(self) -> None:
    """Theoretical robustness: if two franchises share a nickname,
    neither gets an alias (matches pass 4b semantics at line 406)."""
    name_map = {"F_A": "Alpha Team", "F_B": "Beta Team"}
    nickname_map = {"F_A": "Ace", "F_B": "Ace"}  # collision
    reverse = _build_reverse_name_map(name_map, nickname_map=nickname_map)
    assert "ace" not in reverse
```

Assert targets: `"ace" not in reverse` pins collision-suppression
semantics. Matches pass 4b's `if len(fids) != 1: continue` at line 406.

### Q10 — Unit vs integration level

**Unit level at `_build_reverse_name_map`.** All four fixtures pass
literal dicts as input; no DB, no loader, no verifier lifecycle.
This matches the existing owner-alias test at line 258-262.

Integration-level coverage (real DB with `franchise_nicknames`
populated) is not required for this implementation pass. The
existing live-DB-mirror test at line 2462 implicitly covers
backward compatibility via `owner_map={}` and `nickname_map` defaulted
to `None`; see Q11. A dedicated integration test for the nickname
loader may be a separate follow-up but is not scoped into the
Option B implementation session.

### Q11 — Backward compatibility with the live-DB-mirror test at line 2462

Current invocation: `_build_reverse_name_map(name_map, owner_map={})`.

Proposed signature: `_build_reverse_name_map(name_map, owner_map=None, nickname_map=None)`.

Both changes are backward compatible:
- `owner_map={}` → still a valid non-None value; pass 4b sees empty
  dict and does nothing (the `if owner_map:` guard at line 388 is
  falsy for `{}` as it is today).
- `nickname_map` omitted → defaults to `None`; pass 4a's `if nickname_map:`
  guard is falsy for `None`.

Net effect: zero change required to the live-DB-mirror test.
All three `"<alias>" not in reverse` assertions at lines 272,
292, 301 continue to hold because passes 1–3 and pass 4b run
identically.

---

## Auth-plumbing boundary axis — Q12, Q13, Q14

### Q12 — Does Option B implementation require re-ingesting `owner_name`?

**Branch (a) selected: nickname-only. Option (ii) is not a precondition.**

Evidence (ranked by load-bearing weight):

1. **Zero-consumer `owner_name` beyond alias derivation.** Grep at
   `src/squadvault/ — owner_name` returns results only in
   `_run_franchises_ingest.py` (the write path itself) and
   `recap_verifier_v1.py` (the four references at lines 174, 179,
   190, 2944 — all part of `_load_franchise_owner_names → pass-4b`).
   No other production consumer reads `owner_name`. If nickname
   aliases supersede pass-4b for the four critical franchises
   (0002/KP, 0003/Pat, 0005/Steve, 0009/Michele), `owner_name`'s
   population status becomes observationally irrelevant to the
   verifier. The F6-KP attribution failure from the 04-20
   APPROVED_STREAK memo resolves via nickname `KP`, not via
   owner first-word extraction.

2. **Shape-A franchises (Pat/Steve/Michele) still resolve via pass 4b
   when curated.** The nickname layer supplies the same alias
   (`pat`, `steve`, `michele`) that pass-4b would have extracted
   had `owner_name` been populated. Populating `owner_name` in
   addition to nickname would be redundant for these three.

3. **Shape-B franchise (0002/KP) does not benefit from `owner_name`
   population.** The 04-19 memo classified 0002 as Shape B because
   MFL returned `Kent Paradis` under forced auth. Populating
   `owner_name = 'Kent Paradis'` in `franchise_directory` would
   produce pass-4b alias `kent` — which is the dead-alias case.
   Option B was selected precisely because owner_name alone does
   not fix this franchise. Re-ingesting owner_name (the Option (ii)
   chain) delivers no resolution the nickname layer does not also
   deliver.

4. **Long dependency chain under branch (b).** Branch (b) sequencing
   would be: Option (ii) scope → Option (ii) impl (across three
   unauth write paths: `client.py:149`, `discovery._probe_season`,
   `historical_ingest` cache preference at line 99-100) →
   Option B scope [this memo] → Option B impl → re-ingest execution
   across 17 seasons → re-verification. Branch (a) skips everything
   before "Option B impl" and the re-ingest step.

The combination is decisive. Branch (a) is not a soft-sell of the
simpler path — it is the only path under which the KP dead-alias
actually resolves with minimum blast radius.

### Q13 — Forward-compatibility if `owner_name` population is added later

Under branch (a), future population of `owner_name` is **additive and
non-disruptive**:

- The nickname pass 4a continues to populate `kp`, `pat`, `steve`,
  `michele`.
- Pass 4b would additionally populate `kent` (for F_KP, incidental),
  `pat` (collides with pass 4a via non-override — pass 4a wins,
  which is what we want), `steve`, `michele`.

Net reverse-map shape under future Option (ii) + branch (a)
coexistence:

```
reverse["kp"] = F_KP        # pass 4a
reverse["kent"] = F_KP      # pass 4b (incidental; harmless)
reverse["pat"] = F_PAT      # pass 4a (pass 4b non-override)
reverse["steve"] = F_WEICHERT  # pass 4a (pass 4b non-override)
reverse["michele"] = F_CAVALLINI  # pass 4a (pass 4b non-override)
```

No conflict. No behavioral regression. The nickname layer composes
cleanly with a later `owner_name` population pass if one is
undertaken.

**Schema forward-compatibility:** Option S2's `franchise_nicknames`
table is fully independent of `franchise_directory.owner_name`.
Neither references the other. Adding population logic for
`owner_name` later does not require any change to
`franchise_nicknames` or its loader.

### Q14 — Branch (b) sequencing (documented for completeness, not recommended)

If a future session determines that `owner_name` population is
independently worth pursuing (e.g. for a use case beyond alias
derivation that does not exist today), the sequence would be:

1. Option (ii) scoping — enumerate auth-plumbing changes across the
   three unauth write paths flagged in the 04-19 decision memo's
   incidental finding (`client.py:149`, `discovery._probe_season`,
   `historical_ingest._ingest_franchise_info` cache preference at
   line 99-100). That scoping pass is itself a distinct brief.
2. Option (ii) implementation — src/Tests changes across `client.py`,
   `discovery.py`, `historical_ingest.py`. Has its own test
   coverage expansion for the forced-auth path.
3. Re-ingest execution for 17 seasons under forced auth. DB mutation
   window.
4. Re-verification via `scripts/verify_season.py` to confirm
   `owner_name` population and continued verifier behavior.

This sequence is **not a precondition** for Option B implementation
under branch (a). It is offered here only to document what the
alternative path would entail, so that future readers do not
re-derive it.

---

## Headline selections

- **Schema:** Option S2 — new table `franchise_nicknames` keyed
  `(league_id, franchise_id)`, cross-season, commissioner-curated.
  Migration `0010_add_franchise_nicknames.sql`.
- **Code:** Option C3 — pre-pass-4 injection, pass 4 renumbered to
  4a (curated nickname) + 4b (owner first-word, unchanged body).
  Separate loader `_load_franchise_nicknames` in
  `recap_verifier_v1.py` alongside `_load_franchise_owner_names`.
- **Regression tests:** 4 fixtures at the `_build_reverse_name_map`
  unit level, new `TestBuildReverseNameMapNickname` class adjacent
  to existing tests at `Tests/test_recap_verifier_v1.py:258-262`.
  Live-DB-mirror test at line 2462 unchanged (backward compat via
  `nickname_map=None` default).
- **Auth-plumbing boundary:** Branch (a) — nickname-only. Option (ii)
  is **not** a precondition for Option B implementation.

---

## Preconditions for the implementation session

The Option B implementation session can begin immediately. Required
state and inputs:

1. **HEAD pinned to `3e4dabc`** (this memo's commit + `3e4dabc`,
   whichever is the scoping-memo commit).
2. **No credentials required.** No MFL probes, no re-ingest.
3. **Pre-curated nickname values for the 10 franchises** — derived
   from the 04-19 memo's classification table. The values are:
   `0001 → Stu`, `0002 → KP`, `0003 → Pat`, `0004 → Eddie`,
   `0005 → Steve`, `0006 → Miller` (pass-2 first-word already
   yields this; curating is still safe and forward-compatible),
   `0007 → Robb`, `0008 → Ben`, `0009 → Michele`,
   `0010 → Brandon`. Only the four critical franchises are strictly
   required for F6-KP resolution; the other six are defensive and
   keep the curation table complete.
   **Note:** This is enumeration, not a curation decision. The
   implementation session will surface the values as test fixtures
   and as DDL-insert-statement examples; the operator's curation
   of `franchise_nicknames` for production DB is a post-migration
   step distinct from code/test delivery.
4. **Implementation session deliverables:**
   - New migration `0010_add_franchise_nicknames.sql`.
   - New function `_load_franchise_nicknames` in
     `recap_verifier_v1.py`.
   - `_build_reverse_name_map` signature extended with
     `nickname_map: dict[str, str] | None = None`.
   - Pass 4 renumbered and split into 4a (new) + 4b (existing body,
     unchanged).
   - Call site at `recap_verifier_v1.py:2944-2945` updated (one line added).
   - Call site at `scripts/verify_season.py:112` updated (one line added).
   - `Tests/test_recap_verifier_v1.py` updated with the four N1–N4
     fixtures in a new test class.
5. **Pre-commit gates:** ruff clean (`src/`), mypy unchanged, full
   pytest suite passing (baseline 1849 passed, 2 skipped, plus 4 new).
6. **One-topic discipline:** the implementation pass delivers schema +
   code + tests as a single coherent commit. Commissioner curation
   (actual `INSERT` statements into `franchise_nicknames` for PFL
   Buddies) is a separate, post-implementation step and commit.
7. **No ingest runs, no re-verification pass in the implementation
   session itself.** Verifier behavior change is validated via the
   four new unit fixtures, not via re-running the 04-20
   APPROVED_STREAK failure set. Re-running that failure set against
   the post-curation DB is a separate observation pass.

---

## Out of scope (what this pass did NOT do)

- No `src/` changes.
- No `Tests/` changes.
- No new files in `scripts/`.
- No DB access of any kind (no reads, no mutations).
- No MFL API calls.
- No commissioner curation of `franchise_nicknames` values
  (enumeration of expected values per the 04-19 memo's classification
  table is not the same as DB writes; those land post-migration).
- Option (ii) implementation — fully deferred; not a precondition
  for Option B.
- Option A execution — superseded by the 04-19 decision.
- `waiver_bids.py` ingest promotion.
- `deterministic_bullets_v1.py` consumer-layer leak pass.
- `audit_queries/README.md` catalog update (still deferred housekeeping;
  offered as Alt A in the session brief).
- `.env.local` export discipline (brief Alt B; 30-second user-machine
  edit; not a commit).
- The four untracked `scripts/diagnose_*.py` entries.
- No amendment of the 04-21 pre-read (`ecbc1d4`), the 04-21 audit-
  query memo (`83ea9d3`), the 04-21 auth-blocker memo (`c001a8c`),
  or the 04-19 decision memo (`3e4dabc`).

---

## Cross-references

- **Upstream decision memo:** `3e4dabc` —
  `_observations/OBSERVATIONS_2026_04_19_OWNER_NAME_STEP5_DECISION.md`.
  Selects Option B mechanically via pre-read decision rule; 0002
  Shape B; incidental three-unauth-write-paths finding that
  reframes Option (ii) scope.
- **Upstream auth-blocker memo:** `c001a8c` —
  `_observations/OBSERVATIONS_2026_04_21_OWNER_NAME_STEP5_AUTH_BLOCKER.md`.
  Risk 2 confirmed; original Option (ii) framing (client.py:149
  retry-gate change).
- **Upstream pre-read:** `ecbc1d4` —
  `_observations/OBSERVATIONS_2026_04_21_OWNER_NAME_POPULATION_PREREAD.md`.
  Option A/B/C space; resolution-probability matrix; rubric; named
  risks.
- **Attribution-failure context:** 2026-04-20 APPROVED_STREAK memo —
  F6-KP attribution failure is the load-bearing case Option B
  resolves.
- **Pass-4 alias derivation source:**
  `src/squadvault/core/recaps/verification/recap_verifier_v1.py:381-410`.
- **Migration convention:**
  `src/squadvault/core/storage/migrations/0001-0009*.sql`,
  managed by `src/squadvault/core/storage/migrate.py`. Schema DDL
  canonical in `schema.sql:111-126` (franchise_directory);
  voice-profile precedent at `schema.sql:328-346` + migration 0006.
- **Loader callers:**
  `recap_verifier_v1.py:2944` (canonical lifecycle entry),
  `scripts/verify_season.py:112` (batch season scan).
- **Live-DB-mirror test backward-compat anchor:**
  `Tests/test_recap_verifier_v1.py:2462`.

---

## Observation-time state

- HEAD at observation-time: `3e4dabc`.
- Test baseline unchanged: 1849 passed, 2 skipped.
- Ruff: 0 errors (`src/`); 238 pre-existing in `Tests/` (unchanged).
- Mypy: 0 errors (`src/squadvault/core/`); 59 source files clean.
- No `src/` or `Tests/` changes in this session.
- No DB mutations, no ingest runs, no MFL probes.
- Staging gate: one file staged (this memo).
- One-topic discipline: "scope Option B across four design axes."

---

## Commit message template

```
Phase 10 scoping: Option B — nickname override layer

Owner-name alias decision memo (3e4dabc) selected Option B. This
scoping pass enumerates the design space across schema, code,
regression tests, and auth-plumbing boundary, and selects S2 + C3 +
branch (a) for the implementation pass.

Headline selections:
  - Schema: new table `franchise_nicknames` keyed
    (league_id, franchise_id), cross-season, commissioner-curated.
    Migration 0010.
  - Code: pre-pass-4 injection; pass 4 renumbered to 4a (curated
    nickname) + 4b (owner first-word, body unchanged). Separate
    loader `_load_franchise_nicknames` alongside
    `_load_franchise_owner_names`.
  - Regression tests: 4 fixtures at _build_reverse_name_map unit
    level, adjacent to existing tests at line 258-262. Live-DB-
    mirror test at 2462 unchanged via nickname_map=None default.
  - Auth-plumbing boundary: branch (a) — nickname-only. Option (ii)
    not a precondition. Grounded in the observation that
    owner_name's only src/ consumer is pass-4b alias derivation;
    nickname layer supersedes that for the four critical
    franchises without any owner_name population work.

Next session scope: Option B implementation (schema migration,
_build_reverse_name_map change, four unit-level regression fixtures).
Credentials not needed; no re-ingest step.

HEAD at observation-time: 3e4dabc.
Test baseline unchanged (1849 passed, 2 skipped).
No src/ or Tests/ changes. No DB mutations, no ingest runs.
```
