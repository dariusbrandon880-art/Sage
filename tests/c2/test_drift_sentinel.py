"""Unit tests for Flight D: Fresh-Session Drift Sentinel."""

import time
from sage.c2.directive_fidelity import DirectiveFingerprint
from sage.c2.drift_sentinel import DriftReplayScenario, DriftSentinel
from sage.c2.reality_gate import OperationalClaim, SourceReceipt


def test_drift_sentinel_clean_scenario():
    instruction = "Check live repo.\nInspect PR.\nDo not merge."
    contract = DirectiveFingerprint.create_contract(instruction)

    receipt = SourceReceipt(
        source_type="github",
        resource_id="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
        sha256_digest="70d1e798d5deee425a138e12ec070c8b10af2793",
        timestamp_utc=time.time(),
    )

    scenario = DriftReplayScenario(
        scenario_id="sc-01",
        user_instruction=instruction,
        contract=contract,
        proposed_actions=("Check live repo", "Inspect PR"),
        proposed_claims=(
            OperationalClaim(
                claim_id="c1",
                statement="GitHub main is at 70d1e798d5deee425a138e12ec070c8b10af2793.",
                required_source_type="github",
                target_resource="commit:70d1e798d5deee425a138e12ec070c8b10af2793",
            ),
        ),
        available_receipts=(receipt,),
        expected_should_pass=True,
    )

    is_passed, violations, scores = DriftSentinel.evaluate_scenario(scenario)
    assert is_passed is True
    assert len(violations) == 0
    assert scores["order_fidelity"] == 1.0
    assert scores["source_fidelity"] == 1.0


def test_drift_sentinel_catches_unauthorized_merge_and_fake_claim():
    instruction = "Check live repo.\nDo not merge."
    contract = DirectiveFingerprint.create_contract(instruction)

    scenario = DriftReplayScenario(
        scenario_id="sc-02",
        user_instruction=instruction,
        contract=contract,
        proposed_actions=("Check live repo", "Merge PR"),
        proposed_claims=(
            OperationalClaim(
                claim_id="c1",
                statement="GitHub PR #247 is merged and clean.",
                required_source_type="github",
            ),
        ),
        available_receipts=(),  # No receipts!
        expected_should_pass=False,
    )

    report = DriftSentinel.run_suite([scenario])
    assert report.total_scenarios == 1
    assert report.passed_scenarios == 1  # Passed evaluating expected_should_pass == False
    assert report.metrics.overall_drift_rate == 0.0
