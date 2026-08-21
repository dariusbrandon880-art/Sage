import pytest

from sage.coordination_events import (
    AGENT_ASSIGNMENT,
    AGENT_COORDINATION_MESSAGE,
    AGENT_HANDOFF,
    record_coordination_event,
)


class _Event:
    def model_dump(self):
        return {
            "event_id": "evt-test",
            "event_type": AGENT_COORDINATION_MESSAGE,
            "actor": "GPT",
            "payload": {"summary": "handoff acknowledged"},
        }


class _Manager:
    def record_event(self, **kwargs):
        self.kwargs = kwargs
        return _Event()


def test_coordination_event_writer_accepts_bounded_message(monkeypatch):
    import sage.experimental.airspace.manager as manager_module

    manager = _Manager()
    monkeypatch.setattr(manager_module, "AirspaceManager", lambda: manager)

    event = record_coordination_event(
        event_type=AGENT_COORDINATION_MESSAGE,
        actor="GPT",
        payload={"summary": "handoff acknowledged"},
        mission_id="mission-1",
        sortie_id="sortie-1",
        evidence_refs=["receipt:test"],
    )

    assert event["event_type"] == AGENT_COORDINATION_MESSAGE
    assert manager.kwargs["mission_id"] == "mission-1"
    assert manager.kwargs["sortie_id"] == "sortie-1"
    assert manager.kwargs["evidence_refs"] == ["receipt:test"]


def test_coordination_event_writer_rejects_authority_mutation_types():
    with pytest.raises(ValueError):
        record_coordination_event(
            event_type="XP_AWARDED",
            actor="GPT",
            payload={"amount": 100},
        )


def test_coordination_event_writer_rejects_empty_actor():
    with pytest.raises(ValueError):
        record_coordination_event(
            event_type=AGENT_HANDOFF,
            actor="   ",
            payload={"to": "Jules"},
        )


def test_coordination_event_writer_rejects_non_mapping_payload():
    with pytest.raises(TypeError):
        record_coordination_event(
            event_type=AGENT_ASSIGNMENT,
            actor="Director",
            payload="not-a-dict",
        )
