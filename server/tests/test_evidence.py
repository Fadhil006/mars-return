import pytest

from server.evidence import PlanStore, trusted_context


def test_store_expiry_eviction_and_copy_isolation():
    now = [0]
    store = PlanStore(max_entries=1, ttl_seconds=10, clock=lambda: now[0])
    inputs = {"datasetVersion": "one"}
    result = {"options": {"shortest": {"distanceM": 10}}}
    first, _ = store.save(inputs, result)
    result["options"]["shortest"]["distanceM"] = 999
    assert trusted_context(store, first, "one", "shortest")["metrics"]["distanceM"] == 10
    with pytest.raises(KeyError):
        store.get(first, "two")
    second, _ = store.save(inputs, result)
    with pytest.raises(KeyError):
        store.get(first, "one")
    now[0] = 10
    with pytest.raises(KeyError):
        store.get(second, "one")


def test_hash_ignores_dict_order_and_context_rejects_wrong_mode():
    store = PlanStore()
    _, a = store.save({"datasetVersion": "one", "x": 1}, {})
    _, b = store.save({"x": 1, "datasetVersion": "one"}, {})
    assert a == b
    identifier, _ = store.save({"datasetVersion": "one", "selectedRouteMode": "shortest"}, {"immediateReturn": {}})
    with pytest.raises(ValueError):
        trusted_context(store, identifier, "one", "slope_penalized")
