"""Bounded trusted evaluation records, shared with B3's assistant adapter."""

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import json
from threading import Lock
from time import monotonic
from uuid import uuid4


class PlanStore:
    def __init__(self, max_entries=128, ttl_seconds=3600, clock=monotonic):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._records = OrderedDict()
        self._lock = Lock()

    def save(self, inputs, result):
        payload = json.dumps(inputs, sort_keys=True, separators=(",", ":"), allow_nan=False)
        identifier = str(uuid4())
        record = {"inputs": deepcopy(inputs), "result": deepcopy(result),
                  "inputHash": sha256(payload.encode()).hexdigest(), "planId": identifier}
        with self._lock:
            now = self.clock()
            self._expire(now)
            self._records[identifier] = (now, record)
            while len(self._records) > self.max_entries:
                self._records.popitem(last=False)
        return identifier, record["inputHash"]

    def _expire(self, now):
        expired = [key for key, (created, _) in self._records.items() if now-created >= self.ttl_seconds]
        for key in expired:
            del self._records[key]

    def get(self, plan_id, dataset_version):
        with self._lock:
            self._expire(self.clock())
            entry = self._records.get(plan_id)
            if entry is None or entry[1]["inputs"]["datasetVersion"] != dataset_version:
                raise KeyError("Plan missing, expired, or stale; recalculate")
            return deepcopy(entry[1])


def trusted_context(store, plan_id, dataset_version, selected_route_mode):
    """Never accept route metrics or evidence supplied by a chat prompt."""
    if selected_route_mode not in ("shortest", "slope_penalized"):
        raise ValueError("Unsupported route mode")
    record = store.get(plan_id, dataset_version)
    result = record["result"]
    if "options" in result:
        metrics = result["options"][selected_route_mode]
    else:
        if record["inputs"]["selectedRouteMode"] != selected_route_mode:
            raise ValueError("Rehearsal route mode differs from saved assessment")
        metrics = result
    return {"planId": plan_id, "datasetVersion": dataset_version,
            "inputHash": record["inputHash"], "metrics": metrics,
            "sourceIds": result.get("sourceIds", []), "modelVersion": result.get("modelVersion")}
