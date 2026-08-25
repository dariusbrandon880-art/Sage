"""Test suite for SAGE Big Build Jump Wave Readiness Receipt and Evidence Artifact.

Validates schema compliance, flight isolation, fail-closed defaults,
and complete repo truth coverage.
"""

import json
from pathlib import Path
import pytest


def test_big_build_jump_wave_readiness_markdown_exists():
    receipt_path = Path("docs/master/SAGE_BIG_BUILD_JUMP_WAVE_READINESS_RECEIPT.md")
    assert receipt_path.exists(), "Readiness receipt Markdown file must exist"
    content = receipt_path.read_text(encoding="utf-8")
    assert "SAGE BIG JUMP WAVE" in content
    assert "REPO TRUTH RECONCILIATION" in content
    assert "FIVE FRONTIER RECONVERGENCE" in content
    assert "FAIL-CLOSED GOVERNANCE POSTURE" in content


def test_big_build_jump_wave_evidence_json_schema():
    evidence_path = Path("evidence_capture/big_build_jump_wave_readiness_receipt.json")
    assert evidence_path.exists(), "Readiness JSON evidence file must exist"
    data = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert data["receipt_type"] == "SAGE_BIG_BUILD_JUMP_WAVE_READINESS_RECEIPT"
    assert data["status"] == "PROVISIONALLY_EVALUATED"
    assert data["is_authorized"] is False, "Default launch status must fail closed (is_authorized=False)"

    # Verify 5 wave 2 frontiers
    flights = data.get("wave_2_frontiers", [])
    assert len(flights) == 5, "Must have exactly 5 wave 2 frontiers"
    flight_ids = [f["flight_id"] for f in flights]
    assert flight_ids == ["F1", "F2", "F3", "F4", "F5"]
