import pytest

from sage.coordination_events import AGENT_COORDINATION_RECEIPT, record_coordination_event


class _Event:
    def __init__(self, event_type):
        self.event_type = event_type

    def model_dump(self):
        return {"event_id": "receipt-test", "event_type": self.event_type, "actor": "C2", "payload": {}}


class _Manager:
    def __init__(self, events):
        self.events = events
        self.recorded = None

    def _load_raw_events(self):
        return list(self.events)

    def record_event(self, **kwargs):
        self.recorded = kwargs
        return _Event(kwargs["event_type"])


def _manager(monkeypatch, events):
    import sage.experimental.airspace.manager as manager_module
    manager = _Manager(events)
    monkeypatch.setattr(manager_module, "AirspaceManager", lambda: manager)
    return manager


def test_valid_receipt_is_append_only(monkeypatch):
    manager = _manager(monkeypatch, [
        {"event_id": "evt-1", "event_type": "AGENT_HANDOFF", "payload": {"recipient": "C2"}},
    ])
    event = record_coordination_event(
        event_type=AGENT_COORDINATION_RECEIPT,
        actor="C2",
        payload={"acknowledged_event_id": "evt-1", "acknowledged_at": "2026-08-21T13:05:00Z"},
    )
    assert event["event_type"] == AGENT_COORDINATION_RECEIPT
    assert manager.recorded["payload"]["acknowledged_event_id"] == "evt-1"


def test_receipt_rejects_cross_agent_ack(monkeypatch):
    _manager(monkeypatch, [
        {"event_id": "evt-2", "event_type": "AGENT_HANDOFF", "payload": {"recipient": "GEMINI"}},
    ])
    with pytest.raises(ValueError, match="cannot acknowledge"):
        record_coordination_event(
            event_type=AGENT_COORDINATION_RECEIPT,
            actor="C2",
            payload={"acknowledged_event_id": "evt-2", "acknowledged_at": "2026-08-21T13:05:00Z"},
        )


@pytest.mark.parametrize("payload", [
    {},
    {"acknowledged_event_id": "evt-1"},
    {"acknowledged_event_id": "evt-1", "acknowledged_at": "not-a-timestamp"},
    {"acknowledged_event_id": "evt-1", "acknowledged_at": "2026-08-21T13:05:00Z", "extra": True},
])
def test_receipt_rejects_malformed_payload(monkeypatch, payload):
    _manager(monkeypatch, [
        {"event_id": "evt-1", "event_type": "AGENT_HANDOFF", "payload": {"recipient": "C2"}},
    ])
    with pytest.raises(ValueError):
        record_coordination_event(event_type=AGENT_COORDINATION_RECEIPT, actor="C2", payload=payload)
