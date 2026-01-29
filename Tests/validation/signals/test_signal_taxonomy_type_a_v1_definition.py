from squadvault.validation.signals.signal_taxonomy_type_a_v1 import SignalTaxonomyTypeAEnforcerV1

def test_definition_requires_typed_bounded_derived(monkeypatch, tmp_path):
    # Stub authority: non-empty enum + mapping
    enforcer = SignalTaxonomyTypeAEnforcerV1.__new__(SignalTaxonomyTypeAEnforcerV1)
    enforcer._valid_types = ["FOO_SIGNAL"]
    enforcer._category_by_type = {"FOO_SIGNAL": "CATEGORY_A"}

    s_ok = {
        "signal_id": "s1",
        "signal_type": "FOO_SIGNAL",
        "taxonomy_category": "CATEGORY_A",
        "derived_from_event_ids": ["e1"],
    }

    res = enforcer.enforce([s_ok])
    assert res.rejected == []
    assert res.accepted_ids == ["s1"]

    s_missing_type = dict(s_ok)
    s_missing_type.pop("signal_type")
    res2 = enforcer.enforce([s_missing_type])
    assert res2.accepted == []
    assert res2.rejected[0].reason == "MISSING_SIGNAL_TYPE"

    s_missing_lineage = dict(s_ok)
    s_missing_lineage.pop("derived_from_event_ids")
    res3 = enforcer.enforce([s_missing_lineage])
    assert res3.accepted == []
    assert res3.rejected[0].reason == "MISSING_DERIVATION_LINEAGE"
