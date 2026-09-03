import json

from scripts.project_git_state import get_active_state


def test_active_state_does_not_invent_legacy_frontier(tmp_path):
    state_file = tmp_path / "sage_state.json"
    state_file.write_text(json.dumps({"snapshots": {"s1": {"timestamp": "2026-09-03T00:00:00Z", "state": {}}}}))
    assert get_active_state(state_file) == ("UNSPECIFIED", "UNBOUND", "UNSPECIFIED")


def test_active_state_reads_governed_snapshot(tmp_path):
    state_file = tmp_path / "sage_state.json"
    state_file.write_text(json.dumps({"snapshots": {"s1": {"timestamp": "2026-09-03T00:00:00Z", "state": {"active_task": "repair", "active_pr": "438", "current_frontier": "flight-boundary"}}}}))
    assert get_active_state(state_file) == ("repair", "438", "flight-boundary")
