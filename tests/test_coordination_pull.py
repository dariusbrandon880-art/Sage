import sage.agent_coordination as coordination


class _State:
    pass


class _ManagerModule:
    class AirspaceManager:
        pass


def _events():
    return [
        {"event_id": "evt-1", "event_type": "AGENT_HANDOFF", "timestamp": "2026-08-21T13:00:00Z", "actor": "GEMINI", "payload": {"recipient": "C2"}},
        {"event_id": "evt-2", "event_type": "AGENT_HANDOFF", "timestamp": "2026-08-21T13:01:00Z", "actor": "GEMINI", "payload": {"recipient": "JULES"}},
        {"event_id": "evt-3", "event_type": "AGENT_CHALLENGE", "timestamp": "2026-08-21T13:02:00Z", "actor": "GEMINI", "payload": {"recipients": ["C2"]}},
        {"event_id": "evt-4", "event_type": "AGENT_COORDINATION_RECEIPT", "timestamp": "2026-08-21T13:03:00Z", "actor": "C2", "payload": {"acknowledged_event_id": "evt-1", "acknowledged_at": "2026-08-21T13:03:00Z"}},
    ]


def _patch(monkeypatch, events):
    monkeypatch.setattr(coordination, "_load", lambda: (_ManagerModule, _State()))
    monkeypatch.setattr(coordination, "_events", lambda manager: events)


def test_unread_projection_filters_acknowledged_events(monkeypatch):
    _patch(monkeypatch, _events())
    assert [e["event_id"] for e in coordination.get_unread_coordination("C2")] == ["evt-3"]


def test_get_unread_is_pure_and_non_mutating(monkeypatch):
    events = _events()
    snapshot = repr(events)
    _patch(monkeypatch, events)
    coordination.get_unread_coordination("C2")
    assert repr(events) == snapshot


def test_duplicate_receipts_are_projection_idempotent(monkeypatch):
    events = _events() + [{"event_id": "evt-5", "event_type": "AGENT_COORDINATION_RECEIPT", "actor": "C2", "payload": {"acknowledged_event_id": "evt-1"}}]
    _patch(monkeypatch, events)
    assert [e["event_id"] for e in coordination.get_unread_coordination("C2")] == ["evt-3"]


def test_cross_agent_receipt_cannot_acknowledge_other_recipient(monkeypatch):
    events = _events() + [{"event_id": "evt-6", "event_type": "AGENT_COORDINATION_RECEIPT", "actor": "JULES", "payload": {"acknowledged_event_id": "evt-3"}}]
    _patch(monkeypatch, events)
    assert [e["event_id"] for e in coordination.get_unread_coordination("C2")] == ["evt-3"]


def test_replay_reconstructs_identical_unread_state(monkeypatch):
    events = _events()
    _patch(monkeypatch, events)
    first = coordination.get_unread_coordination("C2")
    second = coordination.get_unread_coordination("C2")
    assert first == second


def test_receipts_do_not_create_authority_or_progression_mutation(monkeypatch):
    events = _events()
    _patch(monkeypatch, events)
    unread = coordination.get_unread_coordination("C2")
    assert [event["event_id"] for event in unread] == ["evt-3"]
    assert all("xp" not in event and "authority" not in event for event in unread)
