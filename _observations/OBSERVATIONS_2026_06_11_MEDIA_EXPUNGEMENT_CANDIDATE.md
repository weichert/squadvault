# Media expungement class - ADMITTED + DISCHARGED (D-W1-E1)

## STATUS UPDATE 2026-06-11 - PARKED -> ADMITTED -> DISCHARGED

D-W1-E1 ruled (a) 2026-06-11; Spec 5.2 Amendment 1 RATIFIED. Ruling memo of record =
frontend `ff1b74b`. Built + merged in frontend PR #19 (`7119651`); migration 014
(`media_expungement_events`) applied and live on prod; G19 active (probe-skip pattern).
The registration record below is retained verbatim as the historical record; its
"Do not build" instruction is SUPERSEDED by the ruling above.

Dated 2026-06-11. Type: registration record for a DECIDE candidate. **Do not build.**
A build requires its own DECIDE session (spec amendment). Verified at authoring: engine
`weichert/squadvault` main = `926a923`; frontend `c82bd5f` (ingest ergonomics merged).

## Founder need

Truly REMOVE mistaken / duplicate / never-belonged uploads. Display withdrawal (spec
5.5, now with reinstatement, D5) HIDES an item but RETAINS the bytes and its ingest
visibility forever - by design. There is no path today to actually delete content.

## Constitutional shape if pursued (deaccession pattern)

An append-only **expungement EVENT** (commissioner-ratified, reason REQUIRED) that:
- deletes the storage object(s), and
- tombstones the `media_entries` row.

The log forever records that an item existed and was expunged - when, who, why - while
the CONTENT itself is gone. The record of the act is permanent (append-only is preserved
at the event layer); only the bytes and the recoverable entry are removed. This is
deaccession, not erasure of history.

## Why a DECIDE session is required (not a build)

- **Collides with spec 5.2 as written** (retain-the-original / no-deletion). Expungement
  needs a spec amendment, adjudicated in its own DECIDE session - the same discipline as
  D-W1-V1 / Spec 5.1 Amendment 1, not an EXECUTE brief.
- **Post-E2.3 likeness dimension (W.6-adjacent):** a member-requested removal of media OF
  THEMSELVES may legitimately need more than display withdrawal - actual expungement may
  be the correct honoring of a likeness/consent request. This dimension is unreachable
  until members exist (E2.3); it should shape the amendment, not be bolted on later.

## Trigger

Founder call, OR the first real mistaken-upload incident, OR bundled into the
Increment 2 / E2.3 consent work - whichever lands first. Registered + parked 2026-06-11;
no build, no DECIDE session opened.
