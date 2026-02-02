from squadvault.validation.signals.signal_taxonomy_type_a_v1 import SignalTaxonomyTypeAEnforcerV1

def test_category_must_be_exactly_one_and_match_mapping():
    enforcer = SignalTaxonomyTypeAEnforcerV1.__new__(SignalTaxonomyTypeAEnforcerV1)
    enforcer._valid_types = ["FOO_SIGNAL"]
    enforcer._category_by_type = {"FOO_SIGNAL": "CATEGORY_A"}

    base = {
        "signal_id": "s1",
        "signal_type": "FOO_SIGNAL",
        "derived_from_event_ids": ["e1"],
    }

    s0 = dict(base)
    # no category field => reject
    res0 = enforcer.enforce([s0])
    assert res0.rejected[0].reason == "CATEGORY_NOT_EXACTLY_ONE"

    s_multi = dict(base)
    s_multi["taxonomy_category"] = ["CATEGORY_A", "CATEGORY_B"]
    res1 = enforcer.enforce([s_multi])
    assert res1.rejected[0].reason == "CATEGORY_NOT_EXACTLY_ONE"

    s_mismatch = dict(base)
    s_mismatch["taxonomy_category"] = "CATEGORY_B"
    res2 = enforcer.enforce([s_mismatch])
    assert res2.rejected[0].reason == "CATEGORY_MISMATCH_FOR_TYPE"

    s_ok = dict(base)
    s_ok["taxonomy_category"] = "CATEGORY_A"
    res3 = enforcer.enforce([s_ok])
    assert res3.accepted_ids == ["s1"]
