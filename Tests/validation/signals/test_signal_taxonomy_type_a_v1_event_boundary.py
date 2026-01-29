from squadvault.validation.signals.signal_taxonomy_type_a_v1 import SignalTaxonomyTypeAEnforcerV1

def test_event_objects_are_not_signals(monkeypatch):
    enforcer = SignalTaxonomyTypeAEnforcerV1.__new__(SignalTaxonomyTypeAEnforcerV1)
    enforcer._valid_types = ["FOO_SIGNAL"]
    enforcer._category_by_type = {"FOO_SIGNAL": "CATEGORY_A"}

    s_eventish = {
        "signal_id": "s1",
        "signal_type": "FOO_SIGNAL",
        "taxonomy_category": "CATEGORY_A",
        "derived_from_event_ids": ["e1"],
        "event_type": "RAW_EVENT",
    }
    res = enforcer.enforce([s_eventish])
    assert res.accepted == []
    assert res.rejected[0].reason == "EVENT_OBJECT_NOT_A_SIGNAL"

    s_eventish2 = dict(s_eventish)
    s_eventish2.pop("event_type")
    s_eventish2["event_id"] = "ev123"
    res2 = enforcer.enforce([s_eventish2])
    assert res2.accepted == []
    assert res2.rejected[0].reason == "EVENT_OBJECT_NOT_A_SIGNAL"
