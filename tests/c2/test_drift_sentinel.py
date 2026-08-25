"""Unit tests for Flight D: Fresh-Session Drift Sentinel."""

import json
import time
from pathlib import Path

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

    has_drift, violations, scores = DriftSentinel.evaluate_scenario(scenario)
    assert has_drift is False
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
    assert report.passed_scenarios == 1
    assert report.scenarios_with_drift == 1
    assert report.metrics.overall_drift_rate == 1.0


def _write_evidence(path: Path, sha: str, *, flight_sha: str | None = None, verdict: str = "PASS") -> None:
    actual_flight_sha = flight_sha or sha
    data = {
        "commit_sha": sha,
        "wave_verdict": verdict,
        "flight_results": [
            {"flight_id": "Flight A", "status": "PASS", "commit_sha": actual_flight_sha},
            {"flight_id": "Flight B", "status": "PASS", "commit_sha": actual_flight_sha},
        ],
        "summary": {
            "total_flights": 2,
            "passed_flights": 2,
            "wave_verdict": verdict,
            "stale_sha_detected": False,
        },
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_fresh_process_rehydration_rejects_stale_flight_sha(tmp_path):
    expected_sha = "a" * 40
    evidence = tmp_path / "evidence.json"
    _write_evidence(evidence, expected_sha, flight_sha="b" * 40)

    assert DriftSentinel.run_fresh_process_rehydration_check(evidence, expected_sha) is False


def test_fresh_process_rehydration_rejects_inconsistent_summary(tmp_path):
    expected_sha = "a" * 40
    evidence = tmp_path / "evidence.json"
    _write_evidence(evidence, expected_sha)
    data = json.loads(evidence.read_text(encoding="utf-8"))
    data["summary"]["passed_flights"] = 1
    evidence.write_text(json.dumps(data), encoding="utf-8")

    assert DriftSentinel.run_fresh_process_rehydration_check(evidence, expected_sha) is False
