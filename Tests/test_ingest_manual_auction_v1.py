"""Tests for squadvault.ingest.manual_auction (Unit A8, Manual Source Adapter).

Pure-derivation coverage of the frozen Gate-2 plan (adapter-level obligations):
  T4.3  tag-format guard        - malformed provenance refuses entry
  T1.1  determinism            - artifact-native external_id, 67 == 67.0
  T4.1  envelope shape          - DRAFT_PICK / MANUAL:<tag> / MANUAL_AUCTION_WON / retention fields
  T7.3  C4 partial-truth        - unreconciled identity held absent, reported
  T4.2  LOAD_ROSTERS anchor     - off-roster (franchise,player) blocked / held absent
  TA.1  marker-aware selection  - excludes AUCTION_BID, INCLUDES MANUAL_AUCTION_WON (whitelist regression)
  C2/D3 content-addressed hash  - sha256_file
DB-integration obligations (T1.1 re-import no-op, T2.1 coexistence, T3.1 conflict-surfaced,
T5.1 canonical byte-unchanged) live in test_manual_auction_store_v1.py.
"""
from __future__ import annotations

import hashlib

import pytest

from squadvault.ingest.manual_auction import (
    MANUAL_AUCTION_WON,
    AttestedAuctionRow,
    ManualProvenanceError,
    build_roster_seed_index,
    derive_manual_auction_envelopes,
    is_valid_manual_external_source,
    manual_external_source,
    select_auction_winners,
    sha256_file,
    stable_manual_external_id,
)

_TAG = "KP-AUCTION-2021"
_SRC = f"MANUAL:{_TAG}"
_SEED = {("0002", "12171"), ("0005", "9001")}


def _derive(rows, *, seed=_SEED, tag=_TAG):
    return derive_manual_auction_envelopes(
        league_id="70985",
        season=2021,
        tag=tag,
        rows=rows,
        source_artifact_sha256="deadbeef",
        source_artifact_ref="cas/deadbeef",
        roster_seed=seed,
    )


# ── T4.3: tag-format guard ───────────────────────────────────────────
class TestTagGuard:
    def test_valid_tag(self):
        assert manual_external_source(_TAG) == _SRC

    @pytest.mark.parametrize("bad", ["", "   ", " leading", "trailing "])
    def test_blank_or_padded_tag_refused(self, bad):
        with pytest.raises(ManualProvenanceError):
            manual_external_source(bad)

    @pytest.mark.parametrize(
        "src,ok",
        [
            ("MANUAL:KP-AUCTION-2021", True),
            ("MANUAL:", False),
            ("MANUAL:  ", False),
            ("MFL", False),
            ("manual:x", False),
            (None, False),
        ],
    )
    def test_is_valid(self, src, ok):
        assert is_valid_manual_external_source(src) is ok

    def test_derive_raises_on_malformed_tag(self):
        with pytest.raises(ManualProvenanceError):
            _derive([AttestedAuctionRow("0002", "12171", 67)], tag="")


# ── T1.1: determinism (artifact-native only) ─────────────────────────
class TestDeterminism:
    def _eid(self, bid):
        return stable_manual_external_id(
            league_id="70985", season=2021, franchise_id="0002", player_id="12171", bid_amount=bid
        )

    def test_int_and_float_bid_hash_identically(self):
        assert self._eid(67) == self._eid(67.0)

    def test_stable_across_calls(self):
        assert self._eid(67) == self._eid(67)

    def test_differs_by_field(self):
        base = self._eid(67)
        other = stable_manual_external_id(
            league_id="70985", season=2021, franchise_id="0005", player_id="12171", bid_amount=67
        )
        assert base != other

    def test_no_timestamp_dependence(self):
        # Same artifact-native inputs -> identical id regardless of when called (no ts/index term).
        envs1, _ = _derive([AttestedAuctionRow("0002", "12171", 67)])
        envs2, _ = _derive([AttestedAuctionRow("0002", "12171", 67)])
        assert envs1[0]["external_id"] == envs2[0]["external_id"]


# ── T4.1: envelope shape ─────────────────────────────────────────────
class TestEnvelopeShape:
    def test_canonical_manual_envelope(self):
        envs, held = _derive([AttestedAuctionRow("0002", "12171", 67)])
        assert held == []
        assert len(envs) == 1
        e = envs[0]
        assert e["event_type"] == "DRAFT_PICK"
        assert e["external_source"] == _SRC
        assert e["occurred_at"] is None
        assert e["season"] == 2021 and e["league_id"] == "70985"
        p = e["payload"]
        assert p["mfl_type"] == MANUAL_AUCTION_WON
        assert p["franchise_id"] == "0002" and p["player_id"] == "12171"
        assert p["bid_amount"] == 67.0
        assert p["source_artifact_sha256"] == "deadbeef"
        assert p["source_artifact_ref"] == "cas/deadbeef"


# ── T7.3: C4 partial-truth (held absent, reported) ───────────────────
class TestPartialTruth:
    def test_unreconciled_identity_held_absent(self):
        envs, held = _derive([AttestedAuctionRow("", "12171", 67)])
        assert envs == []
        assert len(held) == 1 and "unreconciled identity" in held[0].reason

    def test_missing_player_held_absent(self):
        envs, held = _derive([AttestedAuctionRow("0002", "", 67)])
        assert envs == [] and len(held) == 1


# ── T4.2: LOAD_ROSTERS integrity anchor ──────────────────────────────
class TestRosterAnchor:
    def test_off_roster_blocked(self):
        envs, held = _derive([AttestedAuctionRow("0002", "99999", 67)])  # not on seed
        assert envs == []
        assert len(held) == 1 and "LOAD_ROSTERS anchor" in held[0].reason

    def test_on_roster_admitted(self):
        envs, held = _derive([AttestedAuctionRow("0005", "9001", 12)])
        assert len(envs) == 1 and held == []

    def test_build_roster_seed_index(self):
        events = [
            {"payload": {"franchise_id": "0002", "players_added_ids": ["12171", "12172"]}},
            {"payload": {"franchise_id": "0005", "players_added_ids": "9001|9002"}},
            {"payload": {"franchise_id": "", "players_added_ids": ["x"]}},  # commissioner-init: skip
        ]
        seed = build_roster_seed_index(events)
        assert ("0002", "12171") in seed and ("0005", "9002") in seed
        assert not any(fr == "" for fr, _ in seed)


# ── TA.1: marker-aware selection (whitelist regression) ──────────────
class TestMarkerAwareSelection:
    def test_excludes_bid_includes_manual_and_live_win(self):
        events = [
            {"event_type": "DRAFT_PICK", "external_source": "MFL", "external_id": "a",
             "payload": {"mfl_type": "AUCTION_WON", "player_id": "1"}},
            {"event_type": "DRAFT_PICK", "external_source": "MANUAL:KP-AUCTION-2021", "external_id": "b",
             "payload": {"mfl_type": MANUAL_AUCTION_WON, "player_id": "2"}},
            {"event_type": "DRAFT_PICK", "external_source": "MFL", "external_id": "c",
             "payload": {"mfl_type": "AUCTION_BID", "player_id": "3"}},  # contaminant
        ]
        won = select_auction_winners(events)
        markers = {w["payload"]["mfl_type"] for w in won}
        assert markers == {"AUCTION_WON", MANUAL_AUCTION_WON}  # BID excluded, MANUAL included
        # A whitelist on 'AUCTION_WON' would drop the MANUAL row -> this asserts it is NOT dropped.
        assert any(w["external_source"].startswith("MANUAL:") for w in won)

    def test_dedups_identical_rows(self):
        e = {"event_type": "DRAFT_PICK", "external_source": "MFL", "external_id": "a",
             "payload": {"mfl_type": "AUCTION_WON"}}
        assert len(select_auction_winners([e, dict(e)])) == 1


# ── C2/D3: content-addressed retention hash ──────────────────────────
class TestContentAddress:
    def test_sha256_file(self, tmp_path):
        p = tmp_path / "wb.xlsx"
        p.write_bytes(b"workbook-bytes")
        assert sha256_file(str(p)) == hashlib.sha256(b"workbook-bytes").hexdigest()
