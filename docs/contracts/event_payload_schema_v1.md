# Event Payload Schema — Adapter Contract (v1.0)

**Status:** CANONICAL  
**Applies To:** All ingest adapters (MFL, Sleeper, ESPN, Yahoo, etc.)  
**Defers To:** Core Engine Technical Specification, Canonical Operating Constitution  
**Purpose:** Define the required payload fields for each event type so future platform adapters produce data the engine can consume without modification.

---

## Design Principle

The SquadVault engine is platform-agnostic. Every ingest adapter converts platform-specific API responses into canonical event envelopes with standardized payload fields. The engine (canonicalization, selection, bullet rendering, season context derivation, creative layer) never sees platform-specific data — only these payload contracts.

An adapter is correct if and only if its output conforms to this document.

---

## Event Envelope (All Event Types)

Every event must be wrapped in this envelope:

| Field | Type | Required | Description |
|---|---|---|---|
| `league_id` | string | YES | Canonical league identifier |
| `season` | int | YES | Season year (e.g. 2024) |
| `external_source` | string | YES | Platform identifier (e.g. "MFL", "SLEEPER", "ESPN") |
| `external_id` | string | YES | Stable, deterministic dedup key. Must be identical for the same real-world event across re-ingestion. |
| `event_type` | string | YES | One of the types defined below |
| `occurred_at` | string (ISO-8601) | RECOMMENDED | When the event occurred. NULL is tolerated but degrades weekly window assignment. |
| `payload` | dict | YES | Event-type-specific fields per the schemas below |

**Deduplication guarantee:** `(league_id, season, external_source, external_id)` must be unique per event. The engine uses `INSERT OR IGNORE` — re-ingestion of identical events is a no-op.

---

## WEEKLY_MATCHUP_RESULT

Head-to-head matchup outcome for a single week.

| Payload Field | Type | Required | Description |
|---|---|---|---|
| `week` | int | YES | Week number (1-indexed) |
| `winner_franchise_id` | string | YES | Franchise ID of the winner (or either team if tied) |
| `loser_franchise_id` | string | YES | Franchise ID of the loser (or other team if tied) |
| `winner_score` | string (decimal) | YES | Winner's score, formatted consistently (e.g. "120.50") |
| `loser_score` | string (decimal) | YES | Loser's score |
| `is_tie` | bool | YES | True if scores are equal |

Optional fields (enrichment, not required for engine operation):

| Payload Field | Type | Description |
|---|---|---|
| `home_franchise_id` | string | Home team franchise ID |
| `away_franchise_id` | string | Away team franchise ID |
| `home_score` | string | Home team score |
| `away_score` | string | Away team score |
| `source_url` | string | API URL the data was fetched from |
| `raw_mfl_json` | string | Platform-specific raw JSON (for audit; adapter names this `raw_{platform}_json`) |

**Consumed by:** Season Context Derivation, deterministic bullet rendering, Rivalry Chronicle.

**Season Context depends on this event type.** Without WEEKLY_MATCHUP_RESULT events, the creative layer receives no standings, streaks, or scoring context.

---

## TRANSACTION_TRADE

A completed trade between two teams.

| Payload Field | Type | Required | Description |
|---|---|---|---|
| `franchise_id` | string | CONDITIONAL | Initiating franchise (if platform provides single-franchise perspective) |

**Standard format** (preferred for new adapters):

| Payload Field | Type | Required | Description |
|---|---|---|---|
| `from_franchise_id` | string | YES | Franchise giving up the player |
| `to_franchise_id` | string | YES | Franchise receiving the player |
| `player_id` | string | YES | Player being moved |

**MFL-compatible format** (supported for backward compatibility):

| Payload Field | Type | Required | Description |
|---|---|---|---|
| `raw_mfl_json` | string (JSON) | YES | Contains `franchise`, `franchise2`, `franchise1_gave_up`, `franchise2_gave_up` |

The bullet renderer handles both formats. New adapters SHOULD use the standard format.

**Consumed by:** Deterministic bullet rendering.

---

## WAIVER_BID_AWARDED

A waiver bid that was won (FAAB or priority-based).

| Payload Field | Type | Required | Description |
|---|---|---|---|
| `franchise_id` | string | YES | Franchise that won the bid |
| `player_id` | string | YES | Player acquired |
| `bid` | int or string | RECOMMENDED | Bid amount (FAAB dollar value). Omit if platform has no bid amounts. |

Alternative field names accepted: `team_id` (alias for `franchise_id`), `player` (alias for `player_id`), `amount` (alias for `bid`).

**Consumed by:** Deterministic bullet rendering, FAAB Outcome Insight (future).

---

## TRANSACTION_FREE_AGENT

A free agent acquisition (no waiver bid — direct pickup).

| Payload Field | Type | Required | Description |
|---|---|---|---|
| `franchise_id` | string | YES | Franchise making the pickup |
| `player_id` | string | YES | Player acquired |

Alternative field names accepted: `team_id`, `player`.

**Consumed by:** Deterministic bullet rendering.

---

## DRAFT_PICK

A single draft pick.

| Payload Field | Type | Required | Description |
|---|---|---|---|
| `franchise_id` | string | YES | Franchise making the pick |
| `player_id` | string | YES | Player selected |
| `round` | int | RECOMMENDED | Draft round |
| `pick` | int | RECOMMENDED | Pick number within the round |

Alternative field names accepted: `team_id`, `player`.

**Consumed by:** Deterministic bullet rendering. (Excluded from weekly recaps by default via allowlist; used in draft-specific artifacts.)

---

## Ops/Boundary Events (Not Rendered)

These event types are ingested for completeness and window computation but produce no recap bullets:

| Event Type | Purpose |
|---|---|
| `TRANSACTION_LOCK_ALL_PLAYERS` | Weekly lock boundary marker — used for window computation |
| `TRANSACTION_BBID_AUTO_PROCESS_WAIVERS` | Ops marker — waiver processing timestamp |
| `TRANSACTION_AUTO_PROCESS_WAIVERS` | Ops marker |
| `TRANSACTION_BBID_WAIVER` | Blind bid placement (no outcome yet) — intentionally silent |

**Adapter guidance:** Ingest these if the platform provides them. They improve window boundary precision. If unavailable, window computation falls back to less precise methods.

---

## Directory Tables (Name Resolution)

In addition to events, adapters should populate these directory tables for name resolution:

### franchise_directory

| Column | Type | Required | Description |
|---|---|---|---|
| `league_id` | string | YES | |
| `season` | int | YES | |
| `franchise_id` | string | YES | Must match the IDs used in event payloads |
| `name` | string | YES | Display name (e.g. "Gopher Boys") |

### player_directory

| Column | Type | Required | Description |
|---|---|---|---|
| `league_id` | string | YES | |
| `season` | int | YES | |
| `player_id` | string | YES | Must match the IDs used in event payloads |
| `name` | string | YES | Display name (e.g. "Patrick Mahomes") |

**These are not events.** They are reference data loaded via `INSERT OR REPLACE` and consumed by the rendering layer for name resolution.

---

## Adapter Implementation Checklist

A new platform adapter is complete when:

1. All event types the platform supports are mapped to the schemas above
2. `external_id` is deterministic: re-ingesting the same data produces zero duplicates
3. `franchise_id` and `player_id` values are consistent across event types
4. `franchise_directory` and `player_directory` are populated
5. `occurred_at` timestamps are populated where available
6. Platform-specific raw JSON is preserved in a `raw_{platform}_json` payload field for audit
7. The adapter imports nothing from `squadvault.core` — it only produces event dicts
8. Existing tests pass with the new adapter's output piped through the golden path

---

## Canonical Declaration

This schema is binding for all ingest adapters. Any event type not defined here requires a schema addition (with versioning) before implementation. Adapters must not invent new payload fields that downstream consumers depend on without updating this document.
