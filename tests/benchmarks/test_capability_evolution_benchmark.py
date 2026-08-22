import json
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).parents[2]
RUNNER = ROOT / "benchmarks/capability_evolution/runner.py"
SPEC = importlib.util.spec_from_file_location("capability_evolution_runner", RUNNER)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def scenario():
    return MOD.load_scenario(ROOT / "benchmarks/capability_evolution/scenarios.json")


def test_all_five_fronts_are_declared():
    assert set(MOD.PRIMARY) == {"H1", "H2", "H3", "H4", "H5"}


def test_sage_governed_preserves_evidence_and_avoids_duplicate_rebuild():
    result = MOD.run("SAGE_GOVERNED", scenario())
    measured = MOD.metrics(result, "H5")
    assert measured["evidence_coverage"] == 1.0
    assert measured["duplicate_work_avoided"] == 1
    assert measured["provenance_completeness"] == 1.0
    assert measured["focus_front_evidenced"] is True


def test_ungoverned_parallel_is_not_allowed_to_claim_governed_evidence():
    result = MOD.run("PARALLEL_UNGOVERNED", scenario())
    measured = MOD.metrics(result, "H5")
    assert measured["evidence_coverage"] < 1.0
    assert measured["provenance_completeness"] == 0.0


def test_policies_are_deterministic():
    sc = scenario()
    for policy in MOD.POLICIES:
        a = MOD.metrics(MOD.run(policy, sc), "H1")
        b = MOD.metrics(MOD.run(policy, sc), "H1")
        assert a == b
