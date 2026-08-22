"""Tests for dependency-aware change impact."""

from sage.change_impact import SAGEChangeImpactAnalyzer


def test_declared_dependency_path_requires_revalidation(tmp_path):
    registry_path = tmp_path / "registry.json"
    analyzer = SAGEChangeImpactAnalyzer(
        registry_path=str(registry_path),
        dependency_paths={"CAP-COGNITIVE-KERNEL": ["sage/shared"]},
    )

    report = analyzer.analyze_changes(["sage/shared/decision_helper.py"])
    result = next(r for r in report.impacted_capabilities if r.capability_id == "CAP-COGNITIVE-KERNEL")
    assert result.classification == "REVALIDATION_REQUIRED"
    assert report.revalidation_required is True
