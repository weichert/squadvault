from squadvault.validation.signals.signal_taxonomy_type_a_v1 import SignalTaxonomyTypeAEnforcerV1

def test_empty_enum_rejects_all_signals():
    enforcer = SignalTaxonomyTypeAEnforcerV1.__new__(SignalTaxonomyTypeAEnforcerV1)
    enforcer._valid_types = []  # explicit empty => fail-closed
    enforcer._category_by_type = {"FOO_SIGNAL": "CATEGORY_A"}  # irrelevant under empty enum

    s = {
        "signal_id": "s1",
        "signal_type": "FOO_SIGNAL",
        "taxonomy_category": "CATEGORY_A",
        "derived_from_event_ids": ["e1"],
    }
    res = enforcer.enforce([s])
    assert res.accepted == []
    assert res.rejected[0].reason == "SIGNAL_TYPE_ENUM_EMPTY_FAIL_CLOSED"
