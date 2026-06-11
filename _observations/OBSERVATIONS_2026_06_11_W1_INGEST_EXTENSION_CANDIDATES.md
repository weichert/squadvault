# W.1 ingest-extension candidates - REGISTERED + PARKED

Dated 2026-06-11. Type: registration record (no build, no DECIDE session opened).
Verified at authoring: engine `weichert/squadvault` main = `c5e4bfd`; frontend
ingest-ergonomics work in PR #11 (the drag-drop bulk path these candidates lean on).

Two W.1-scoped ingest conveniences are registered here so they are not re-discovered
from scratch later. **Both are PARKED.** Neither touches the room display, consent
gates, schema, or any frozen surface; neither blocks the voice-attestation DECIDE
session or Increment 2. **Common trigger: the founder's first real shoebox ingest
session** - decide only if the friction each addresses proves actual, not theoretical.

## Candidate 1 - Google Photos Picker import

- **Shape:** the commissioner opens the Google Photos Picker; user-picked items flow
  into the existing grant -> finalize path as ordinary `media_entries` awaiting tags.
- **Why the Picker specifically:** it is the only remaining third-party path. The
  Library API read scopes were removed 2025-03-31; that API now manages only
  app-created content. The Picker is per-item explicit human selection - no library
  access, no sync, no automation.
- **Constitution fit: GOOD.** Every import is an attributed commissioner act (C3);
  items arrive untagged and pass through normal human-ratified provenance.
- **Cost (why parked):** a new foundation carried forever for one importer - a Google
  Cloud project + OAuth consent flow + Google API verification.
- **Zero-build alternative that exists TODAY:** Google Photos -> album -> select all ->
  download -> bulk drag-drop onto ingest (frontend PR #11).
- **Trigger:** after the first real shoebox session - build only if download-and-drag
  friction proves actual rather than theoretical.

## Candidate 2 - EXIF date-proposal at ingest

- **Shape:** at upload, read the EXIF capture date and PRE-FILL the date tag field as a
  PROPOSAL; the commissioner ratifies, edits, or clears it. Nothing is auto-asserted;
  an untouched proposal is never written.
- **Constitution fit: CONDITIONAL.** EXIF is recorded source metadata, not AI
  inference - but the never-AI-guessed / human-ratified rule (D-W1-3) means it MUST
  enter as a proposal requiring an explicit per-item ratification act, and the
  proposal's origin (`exif`) should be visible at ratification. A one-paragraph
  decision note adjudicating "recorded-metadata proposals are admissible iff
  human-ratified per-item" GATES any build.
- **Caveat to record:** EXIF dates on decades-old scans are often the SCAN date, not
  the capture date - the proposal UI must make rejection effortless.
- **Trigger:** same shoebox session - decide alongside Candidate 1 if manual date entry
  proves to be the dominant friction.

## Disposition

Registered + parked, 2026-06-11. No build, no DECIDE session opened. Revisit at the
first real shoebox ingest session; Candidate 2's build is additionally gated on the
recorded-metadata-proposal decision note.
