from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "dispatch_governed_five_flight.py"


def test_dispatch_adapter_is_bounded_to_canonical_wave():
    text = SCRIPT.read_text()
    assert 'WORKFLOW = "main.yml"' in text
    assert 'REF = "main"' in text
    assert 'EXPECTED_FLIGHTS = ("003", "004", "005", "006", "007")' in text
    assert 'SAGE_GITHUB_ACTIONS_TOKEN' in text
    assert 'workflow_dispatch' not in text or 'dispatches' in text


def test_dispatch_adapter_fails_closed_without_token():
    text = SCRIPT.read_text()
    assert 'BLOCKED: SAGE_GITHUB_ACTIONS_TOKEN is required' in text
    assert 'return 2' in text
