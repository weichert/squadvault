# Rivalry Chronicle (v1)

## Enforced By

- `src/squadvault/consumers/rivalry_chronicle_generate_v1.py`
- `src/squadvault/consumers/rivalry_chronicle_approve_v1.py`
- `src/squadvault/chronicle/generate_rivalry_chronicle_v1.py`

League ID: <LEAGUE_ID>
Season: <SEASON>
Week: <WEEK>
State: <STATE>
Artifact Type: RIVALRY_CHRONICLE_V1

## Matchup Summary

## Key Moments

## Stats & Nuggets

## Closing

## Metadata rules

Metadata is a contiguous block of `Key: Value` lines immediately after header (optionally after one blank line).

Required keys:
- League ID
- Season
- Week
- State
- Artifact Type

Artifact Type must be `RIVALRY_CHRONICLE_V1`.

## Normalization rules

- Leading blank lines dropped.
- Header must be first line.
- Metadata upsert semantics: key uniqueness; last-write wins / overwrite.
- If required headings are missing, exporter may append a minimal scaffold (blank line separated).
