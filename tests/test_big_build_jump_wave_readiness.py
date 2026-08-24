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
    assert "SAGE BIG BUILD JUMP WAVE READINESS" in content
    assert "BIG STRIKE FULL CAMPAIGN SUMMARY" in content
    assert "REPO TRUTH & CAPABILITY MAP" in content
    assert "BIG STRIKE WAVE RECONVERGENCE VERDICT: PASS" in content


def test_big_build_jump_wave_evidence_json_schema():
    evidence_path = Path("evidence_capture/big_build_jump_wave_readiness_receipt.json")
    assert evidence_path.exists(), "Readiness JSON evidence file must exist"
    data = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert data["receipt_type"] == "SAGE_BIG_BUILD_JUMP_WAVE_READINESS_RECEIPT"
    assert data["status"] == "READY_FOR_C2_AUTHORIZATION_GATE"
    assert data["is_authorized"] is False, "Default launch status must fail closed (is_authorized=False)"

    # Verify 5 flight candidates
    flights = data.get("flight_candidates", [])
    assert len(flights) == 5, "Must have exactly 5 flight candidates"
    flight_ids = [f["flight_id"] for f in flights]
    assert flight_ids == ["F1", "F2", "F3", "F4", "F5"]

    # Verify classifications
    classifications = data.get("inventory_classifications", {})
    assert classifications.get("c2_systems") == "COMPLETE"
    assert classifications.get("failure_memory_feedback_loop") == "UNFINISHED"

    # Verify new SAGE themes
    themes = data.get("new_sage_themes", [])
    assert len(themes) == 2, "Must specify exactly two new SAGE capability themes"
