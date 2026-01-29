from squadvault.validation.signals.signal_taxonomy_type_a_v1 import SignalTaxonomyTypeAEnforcerV1

def test_ambiguity_fail_closed_unknown_type_rejected():
    enforcer = SignalTaxonomyTypeAEnforcerV1.__new__(SignalTaxonomyTypeAEnforcerV1)
    enforcer._valid_types = ["FOO_SIGNAL"]
    enforcer._category_by_type = {"FOO_SIGNAL": "CATEGORY_A"}

    s_unknown = {
        "signal_id": "s1",
        "signal_type": "BAR_SIGNAL",
        "taxonomy_category": "CATEGORY_A",
        "derived_from_event_ids": ["e1"],
    }
    res = enforcer.enforce([s_unknown])
    assert res.accepted == []
    assert res.rejected[0].reason == "UNKNOWN_SIGNAL_TYPE"
