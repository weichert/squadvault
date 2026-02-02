from squadvault.validation.signals.signal_taxonomy_type_a_v1 import SignalTaxonomyTypeAEnforcerV1

def test_truth_boundaries_forbid_inference_like_fields():
    enforcer = SignalTaxonomyTypeAEnforcerV1.__new__(SignalTaxonomyTypeAEnforcerV1)
    enforcer._valid_types = ["FOO_SIGNAL"]
    enforcer._category_by_type = {"FOO_SIGNAL": "CATEGORY_A"}

    base = {
        "signal_id": "s1",
        "signal_type": "FOO_SIGNAL",
        "taxonomy_category": "CATEGORY_A",
        "derived_from_event_ids": ["e1"],
    }

    s_bad = dict(base)
    s_bad["motive"] = "because reasons"
    res = enforcer.enforce([s_bad])
    assert res.accepted == []
    assert res.rejected[0].reason == "FORBIDDEN_INFERENCE_FIELDS_PRESENT"
