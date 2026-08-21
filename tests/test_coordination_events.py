import pytest

from sage.coordination_events import (
    AGENT_ASSIGNMENT,
    AGENT_COORDINATION_MESSAGE,
    AGENT_COORDINATION_RECEIPT,
    AGENT_HANDOFF,
    record_coordination_event,
)


class _Event:
    def __init__(self, event_type=AGENT_COORDINATION_MESSAGE):
        self.event_type = event_type

    def model_dump(self):
        return {"event_id": "evt-test", "event_type": self.event_type, "actor": "GPT", "payload": {}}


class _Manager:
    def record_event(self, **kwargs):
        self.kwargs = kwargs
        return _Event(kwargs["event_type"])


def test_coordination_event_writer_accepts_bounded_message(monkeypatch):
    import sage.experimental.airspace.manager as manager_module
    manager = _Manager()
    monkeypatch.setattr(manager_module, "AirspaceManager", lambda: manager)
    event = record_coordination_event(event_type=AGENT_COORDINATION_MESSAGE, actor="GPT", payload={"summary": "handoff acknowledged"}, mission_id="mission-1", sortie_id="sortie-1", evidence_refs=["receipt:test"])
    assert event["event_type"] == AGENT_COORDINATION_MESSAGE
    assert manager.kwargs["mission_id"] == "mission-1"


def test_receipt_requires_validated_payload(monkeypatch):
    import sage.experimental.airspace.manager as manager_module
    monkeypatch.setattr(manager_module, "AirspaceManager", lambda: _Manager())
    event = record_coordination_event(event_type=AGENT_COORDINATION_RECEIPT, actor="C2", payload={"acknowledged_event_id": "evt-100", "acknowledged_at": "2026-08-21T13:05:00Z"})
    assert event["event_type"] == AGENT_COORDINATION_RECEIPT


@pytest.mark.parametrize("payload", [{}, {"acknowledged_event_id": ""}, {"acknowledged_event_id": "evt-1", "acknowledged_at": "bad"}])
def test_receipt_rejects_malformed_payload(payload):
    with pytest.raises(ValueError):
        record_coordination_event(event_type=AGENT_COORDINATION_RECEIPT, actor="C2", payload=payload)


def test_coordination_event_writer_rejects_authority_mutation_types():
    with pytest.raises(ValueError):
        record_coordination_event(event_type="XP_AWARDED", actor="GPT", payload={"amount": 100})


def test_coordination_event_writer_rejects_empty_actor():
    with pytest.raises(ValueError):
        record_coordination_event(event_type=AGENT_HANDOFF, actor="   ", payload={"to": "Jules"})


def test_coordination_event_writer_rejects_non_mapping_payload():
    with pytest.raises(TypeError):
        record_coordination_event(event_type=AGENT_ASSIGNMENT, actor="Director", payload="not-a-dict")
