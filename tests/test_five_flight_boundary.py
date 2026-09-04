from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "sage-five-mission-wave.yml"


def test_five_flight_workflow_uses_execution_units_not_domain_owners():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert 'flight: "003"' in text
    assert 'flight: "004"' in text
    assert 'flight: "005"' in text
    assert 'flight: "006"' in text
    assert 'flight: "007"' in text

    forbidden_domain_bindings = (
        "google-drive-continuity",
        "sports-scientific-integrity",
        "cognitive-pfc-compound",
        "evidence-lineage-replay",
        "progression-receipt-control-tower",
    )
    for binding in forbidden_domain_bindings:
        assert binding not in text

    assert "adaptive execution units" in text
    assert "not a flight identity" in text
