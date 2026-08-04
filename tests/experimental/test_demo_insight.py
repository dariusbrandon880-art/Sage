"""Unit test suite for the SAGE Demonstration Insight Experience layer."""

import os
from sage.experimental.act.demo_insight import DemoInsightExperience


def test_demo_insight_experience_defaults():
    """Verify loading default files and fallbacks for demo insight experience."""
    insight = DemoInsightExperience(
        scenario_evidence_path="nonexistent_file_a.json",
        phase_4_evidence_path="nonexistent_file_b.json"
    )

    # Test load_json fallback
    assert insight.load_json("nonexistent.json") is None

    # Test key insight summary formatting and fallbacks
    summary = insight.get_key_insight_summary()
    assert "SAGE DEMONSTRATION KEY INSIGHT SUMMARY" in summary
    assert "Active Validation" in summary

    # Test why this matters presentation
    why = insight.get_why_this_matters()
    assert "WHY THIS MATTERS" in why
    assert "Cryptographic Lineage Chains" in why

    # Test timeline presentation fallbacks
    timeline = insight.get_decision_timeline()
    assert "SAGE DECISION TIMELINE PRESENTATION" in timeline
    assert "Step 1" in timeline

    # Test operator takeaway summary
    takeaway = insight.get_operator_takeaway()
    assert "OPERATOR TAKEAWAY SUMMARY" in takeaway
    assert "Governance Overheads Reduced" in takeaway

    # Test readable evidence highlights
    highlights = insight.get_readable_evidence_highlights()
    assert "SAGE READABLE EVIDENCE HIGHLIGHTS" in highlights
    assert "Boundary Integrity Status" in highlights

    # Verify rendering aggregates all components cleanly
    all_rendered = insight.render_all()
    assert "SAGE DEMONSTRATION KEY INSIGHT SUMMARY" in all_rendered
    assert "WHY THIS MATTERS" in all_rendered
    assert "SAGE DECISION TIMELINE PRESENTATION" in all_rendered
    assert "OPERATOR TAKEAWAY SUMMARY" in all_rendered
    assert "SAGE READABLE EVIDENCE HIGHLIGHTS" in all_rendered


def test_demo_insight_experience_with_real_files():
    """Verify loading actual files works and extracts dynamic metrics."""
    insight = DemoInsightExperience()

    # Verify parsing succeeds with real files
    summary = insight.get_key_insight_summary()
    assert "SAGE DEMONSTRATION KEY INSIGHT SUMMARY" in summary

    timeline = insight.get_decision_timeline()
    assert "SAGE DECISION TIMELINE PRESENTATION" in timeline

    highlights = insight.get_readable_evidence_highlights()
    assert "SAGE READABLE EVIDENCE HIGHLIGHTS" in highlights
