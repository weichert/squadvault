"""Phase 1C — Canonicalization Idempotency Property Test.

Invariant: For any given (league_id, season) scope, running canonicalize
twice with the same memory_events ledger must produce identical
canonical_events.

Uses hypothesis to generate randomized event sets and verify this
property holds across diverse inputs.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from squadvault.core.canonicalize.run_canonicalize import canonicalize

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "squadvault" / "core" / "storage" / "schema.sql"
LEAGUE = "prop_test_league"
SEASON = 2024


def _fresh_db(tmp_path_factory, idx: int = 0) -> str:
    """Create a fresh DB from schema.sql."""
    db_dir = tmp_path_factory.mktemp(f"propdb_{idx}")
    db_path = str(db_dir / "test.sqlite")
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA_PATH.read_text())
    con.close()
    return db_path


def _insert_events(db_path: str, events: list[dict]) -> None:
    """Bulk-insert memory events."""
    con = sqlite3.connect(db_path)
    for i, evt in enumerate(events):
        con.execute(
            """INSERT INTO memory_events
               (league_id, season, external_source, external_id,
                event_type, occurred_at, ingested_at, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                LEAGUE, SEASON, "prop_test", f"prop_{i}",
                evt["event_type"], evt["occurred_at"],
                "2024-10-01T13:00:00Z",
                json.dumps(evt["payload"]),
            ),
        )
    con.commit()
    con.close()


def _snapshot(db_path: str) -> set[tuple]:
    """Capture semantically meaningful canonical state.

    Returns set of (action_fingerprint, best_memory_event_id, best_score, event_type).
    """
    con = sqlite3.connect(db_path)
    rows = con.execute(
        """SELECT action_fingerprint, best_memory_event_id, best_score, event_type
           FROM canonical_events
           WHERE league_id = ? AND season = ?
           ORDER BY action_fingerprint""",
        (LEAGUE, SEASON),
    ).fetchall()
    con.close()
    return set(rows)


# ── Hypothesis strategies for event generation ────────────────────────

franchise_ids = st.sampled_from(["F01", "F02", "F03", "F04", "F05"])
player_ids = st.sampled_from(["P100", "P200", "P300", "P400", "P500", "P600"])
bid_amounts = st.sampled_from(["0", "5", "10", "25", "50", "100"])
occurred_timestamps = st.sampled_from([
    "2024-10-01T12:00:00Z",
    "2024-10-02T12:00:00Z",
    "2024-10-03T12:00:00Z",
    "2024-10-04T12:00:00Z",
    "2024-10-05T12:00:00Z",
])

waiver_bid_events = st.fixed_dictionaries({
    "event_type": st.just("WAIVER_BID_AWARDED"),
    "occurred_at": occurred_timestamps,
    "payload": st.fixed_dictionaries({
        "franchise_id": franchise_ids,
        "player_id": player_ids,
        "bid_amount": bid_amounts,
    }),
})

free_agent_events = st.fixed_dictionaries({
    "event_type": st.just("TRANSACTION_FREE_AGENT"),
    "occurred_at": occurred_timestamps,
    "payload": st.fixed_dictionaries({
        "franchise_id": franchise_ids,
        "players_added_ids": st.lists(player_ids, min_size=0, max_size=2),
        "players_dropped_ids": st.lists(player_ids, min_size=0, max_size=2),
    }),
})

draft_pick_events = st.fixed_dictionaries({
    "event_type": st.just("DRAFT_PICK"),
    "occurred_at": occurred_timestamps,
    "payload": st.fixed_dictionaries({
        "franchise_id": franchise_ids,
        "player_id": player_ids,
        "round": st.integers(min_value=1, max_value=15),
        "pick": st.integers(min_value=1, max_value=200),
    }),
})

mixed_events = st.lists(
    st.one_of(waiver_bid_events, free_agent_events, draft_pick_events),
    min_size=1,
    max_size=20,
)


# ── Property tests ────────────────────────────────────────────────────

@given(events=mixed_events)
@settings(max_examples=30, deadline=5000)
def test_canonicalize_idempotent_across_randomized_events(events, tmp_path_factory):
    """Running canonicalize twice on the same ledger produces identical results.

    This is the core governance invariant: canonical projections are deterministic
    and reproducible. The scoring function is the sole authority for "best" selection.
    """
    db_path = _fresh_db(tmp_path_factory)

    # Deduplicate external_ids (hypothesis may generate duplicates)
    seen = set()
    unique_events = []
    for evt in events:
        key = f"{evt['event_type']}_{evt['occurred_at']}_{json.dumps(evt['payload'], sort_keys=True)}"
        if key not in seen:
            seen.add(key)
            unique_events.append(evt)

    assume(len(unique_events) > 0)

    _insert_events(db_path, unique_events)

    # First run
    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)
    snapshot_1 = _snapshot(db_path)

    # Second run (canonicalize rebuilds from scratch each time)
    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)
    snapshot_2 = _snapshot(db_path)

    assert snapshot_1 == snapshot_2, (
        "Canonicalization must be idempotent: running twice with the same "
        "ledger must produce identical canonical_events."
    )


@given(events=mixed_events)
@settings(max_examples=30, deadline=5000)
def test_canonicalize_reconstructable_after_wipe(events, tmp_path_factory):
    """After wiping canonical_events and rebuilding, the projection is identical.

    This strengthens the idempotency test: not just re-running, but actually
    deleting all canonical state and proving it can be fully reconstructed.
    """
    db_path = _fresh_db(tmp_path_factory)

    seen = set()
    unique_events = []
    for evt in events:
        key = f"{evt['event_type']}_{evt['occurred_at']}_{json.dumps(evt['payload'], sort_keys=True)}"
        if key not in seen:
            seen.add(key)
            unique_events.append(evt)

    assume(len(unique_events) > 0)

    _insert_events(db_path, unique_events)

    # Build
    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)
    snapshot_before = _snapshot(db_path)

    # Wipe
    con = sqlite3.connect(db_path)
    con.execute("DELETE FROM canonical_membership WHERE canonical_event_id IN (SELECT id FROM canonical_events WHERE league_id=? AND season=?)", (LEAGUE, SEASON))
    con.execute("DELETE FROM canonical_events WHERE league_id=? AND season=?", (LEAGUE, SEASON))
    con.commit()
    con.close()

    # Rebuild
    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)
    snapshot_after = _snapshot(db_path)

    assert snapshot_before == snapshot_after, (
        "Canonical projection must be fully reconstructable from the immutable ledger."
    )


@given(events=mixed_events)
@settings(max_examples=20, deadline=5000)
def test_memory_events_immutable_through_canonicalization(events, tmp_path_factory):
    """Canonicalization must never modify memory_events (the immutable ledger)."""
    db_path = _fresh_db(tmp_path_factory)

    seen = set()
    unique_events = []
    for evt in events:
        key = f"{evt['event_type']}_{evt['occurred_at']}_{json.dumps(evt['payload'], sort_keys=True)}"
        if key not in seen:
            seen.add(key)
            unique_events.append(evt)

    assume(len(unique_events) > 0)

    _insert_events(db_path, unique_events)

    # Snapshot ledger before
    con = sqlite3.connect(db_path)
    before = con.execute(
        "SELECT id, league_id, season, event_type, occurred_at, ingested_at, payload_json "
        "FROM memory_events ORDER BY id"
    ).fetchall()
    con.close()

    canonicalize(league_id=LEAGUE, season=SEASON, db_path=db_path)

    # Snapshot ledger after
    con = sqlite3.connect(db_path)
    after = con.execute(
        "SELECT id, league_id, season, event_type, occurred_at, ingested_at, payload_json "
        "FROM memory_events ORDER BY id"
    ).fetchall()
    con.close()

    assert before == after, "memory_events (immutable ledger) must never be modified"
