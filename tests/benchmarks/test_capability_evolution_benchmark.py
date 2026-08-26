"""Regression tests for recovered capability-evolution benchmark #208."""
from pathlib import Path
from benchmarks.capability_evolution.runner import load_scenario, metrics, run

def test_sage_governed_policy_is_dependency_aware_and_evidenced():
    scenario=load_scenario(Path("benchmarks/capability_evolution/scenarios.json"))
    result=run("SAGE_GOVERNED",scenario)
    summary=metrics(result,"H1")
    assert summary["evidence_coverage"]==1.0
    assert summary["duplicate_work_avoided"]==1
    assert summary["provenance_completeness"]==1.0
    assert summary["regression_rate"]==0.0

def test_benchmark_is_deterministic():
    scenario=load_scenario(Path("benchmarks/capability_evolution/scenarios.json"))
    assert metrics(run("SAGE_GOVERNED",scenario),"H1")==metrics(run("SAGE_GOVERNED",scenario),"H1")
