from squadvault.recaps.writing_room.selection_set_schema_v1 import (
    build_signal_groupings_v1,
    SignalGroupingExtractorV1,
    GroupBasisCode,
)

def _mk(sig_id: str, scope: str, subject: str, facts):
    return {"id": sig_id, "scope": scope, "subject": subject, "facts": facts}

EX = SignalGroupingExtractorV1(
    get_signal_id=lambda s: s["id"],
    get_scope_key=lambda s: s["scope"],
    get_subject_key=lambda s: s["subject"],
    get_fact_basis_keys=lambda s: s["facts"],
)

def test_grouping_requires_two_signals():
    gs = build_signal_groupings_v1([_mk("b", "TEAM", "T1", ["F1"])], EX)
    assert gs == []

def test_grouping_requires_same_scope_subject_and_shared_fact():
    gs = build_signal_groupings_v1([_mk("a", "TEAM", "T1", ["F1"]), _mk("b", "TEAM", "T1", ["F2"])], EX)
    assert gs == []

    gs = build_signal_groupings_v1([_mk("a", "TEAM", "T1", ["F1"]), _mk("b", "TEAM", "T2", ["F1"])], EX)
    assert gs == []

    gs = build_signal_groupings_v1([_mk("a", "TEAM", "T1", ["F1"]), _mk("b", "LEAGUE", "T1", ["F1"])], EX)
    assert gs == []

def test_grouping_happy_path_is_deterministic():
    signals = [_mk("b", "TEAM", "T1", ["F1"]), _mk("a", "TEAM", "T1", ["F1"]), _mk("c", "TEAM", "T1", ["F2"])]
    g1 = build_signal_groupings_v1(signals, EX)
    g2 = build_signal_groupings_v1(list(reversed(signals)), EX)

    assert g1 == g2
    assert len(g1) == 1
    g = g1[0]
    assert g.group_basis == GroupBasisCode.SHARED_FACT_BASIS
    assert g.signal_ids == ["a", "b"]
    assert isinstance(g.group_id, str) and len(g.group_id) == 64
