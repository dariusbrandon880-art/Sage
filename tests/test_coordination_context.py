import sage.agent_coordination as coordination


class _State:
    def __init__(self):
        self.stations = {}


class _ManagerModule:
    class AirspaceManager:
        pass


def _events():
    return [
        {
            "event_id": "evt-1",
            "event_type": "AGENT_HANDOFF",
            "timestamp": "2026-08-21T13:00:00Z",
            "actor": "GEMINI",
            "payload": {"recipient": "C2", "context_id": "ctx-1"},
        },
        {
            "event_id": "evt-2",
            "event_type": "AGENT_CHALLENGE",
            "timestamp": "2026-08-21T13:02:00Z",
            "actor": "GEMINI",
            "payload": {"recipient": "C2", "context_id": "ctx-2"},
        },
        {
            "event_id": "evt-3",
            "event_type": "AGENT_COORDINATION_RECEIPT",
            "timestamp": "2026-08-21T13:03:00Z",
            "actor": "C2",
            "payload": {
                "acknowledged_event_id": "evt-1",
                "acknowledged_at": "2026-08-21T13:03:00Z",
            },
        },
    ]


def _patch(monkeypatch, events):
    monkeypatch.setattr(coordination, "_load", lambda: (_ManagerModule, _State()))
    monkeypatch.setattr(coordination, "_events", lambda manager: events)
    monkeypatch.setattr(coordination, "_identity_for_actor", lambda state, actor: {"nameplate": f"[SAGE::{actor}]", "read_only": True})


def test_unread_projection_filters_acknowledged_events(monkeypatch):
    _patch(monkeypatch, _events())
    unread = coordination.get_unread_coordination("C2")
    assert [event["event_id"] for event in unread] == ["evt-2"]


def test_unread_projection_carries_structured_identity_and_delivery_semantics(monkeypatch):
    _patch(monkeypatch, _events())
    event = coordination.get_unread_coordination("C2")[0]
    assert event["sender_identity"]["nameplate"] == "[SAGE::GEMINI]"
    assert event["context_id"] == "ctx-2"
    assert event["projection_version"] == "coordination-context-v0.1"
    assert event["delivery_state"] == "PENDING"
    assert event["delivery_semantics"] == "pull_projection_only"
    assert event["read_only"] is True
    assert event["authority"] == "canonical_airspace_state_and_event_ledger"


def test_get_unread_is_pure_and_replay_deterministic(monkeypatch):
    events = _events()
    snapshot = repr(events)
    _patch(monkeypatch, events)
    first = coordination.get_unread_coordination("C2")
    second = coordination.get_unread_coordination("C2")
    assert first == second
    assert repr(events) == snapshot


def test_duplicate_receipts_remain_projection_idempotent(monkeypatch):
    events = _events() + [
        {
            "event_id": "evt-4",
            "event_type": "AGENT_COORDINATION_RECEIPT",
            "actor": "C2",
            "payload": {"acknowledged_event_id": "evt-1"},
        }
    ]
    _patch(monkeypatch, events)
    assert [event["event_id"] for event in coordination.get_unread_coordination("C2")] == ["evt-2"]


def test_other_agents_receipts_do_not_clear_recipient_unread(monkeypatch):
    events = _events() + [
        {
            "event_id": "evt-5",
            "event_type": "AGENT_COORDINATION_RECEIPT",
            "actor": "JULES",
            "payload": {"acknowledged_event_id": "evt-2"},
        }
    ]
    _patch(monkeypatch, events)
    assert [event["event_id"] for event in coordination.get_unread_coordination("C2")] == ["evt-2"]
