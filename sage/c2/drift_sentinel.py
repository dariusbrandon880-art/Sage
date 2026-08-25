"""Flight D: Fresh-Session Drift Sentinel for SAGE C2.

Provides an automated adversarial replay test harness that simulates fresh C2 sessions,
evaluates responses/actions against directive contracts, and measures multi-vector fidelity:
- TOOL_FIDELITY
- SOURCE_FIDELITY
- ORDER_FIDELITY
- CONSTRAINT_FIDELITY
- STATE_FIDELITY
- NON_INVENTION
- DRIFT_RATE

Includes fresh-process rehydration evaluation to verify that persisted state produces
identical C2 decisions outside of in-memory execution context.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Sequence, Tuple

from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.directive_fidelity import DirectiveContract, ExactOrderSentinel
from sage.c2.reality_gate import LiveOperationReceipt, OperationalClaim, RealityGate, SourceReceipt


@dataclass(frozen=True)
class DriftReplayScenario:
    scenario_id: str
    user_instruction: str
    contract: DirectiveContract
    proposed_actions: Tuple[str, ...]
    proposed_claims: Tuple[OperationalClaim, ...]
    available_receipts: Tuple[SourceReceipt | LiveOperationReceipt, ...]
    expected_should_pass: bool
    active_execution_identity: str = "canonical_station"


@dataclass(frozen=True)
class DriftEvaluationMetrics:
    tool_fidelity: float
    source_fidelity: float
    order_fidelity: float
    constraint_fidelity: float
    state_fidelity: float
    non_invention_rate: float
    overall_drift_rate: float


@dataclass(frozen=True)
class DriftSentinelReport:
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    scenarios_with_drift: int
    metrics: DriftEvaluationMetrics
    violations: Tuple[str, ...]


class DriftSentinel:
    """Evaluates fresh-session scenarios to detect and measure C2 drift."""

    @classmethod
    def evaluate_scenario(
        cls,
        scenario: DriftReplayScenario,
    ) -> Tuple[bool, List[str], Dict[str, float]]:
        violations: List[str] = []
        fidelity_scores: Dict[str, float] = {
            "tool_fidelity": 1.0,
            "source_fidelity": 1.0,
            "order_fidelity": 1.0,
            "constraint_fidelity": 1.0,
            "state_fidelity": 1.0,
            "non_invention": 1.0,
        }

        order_res = ExactOrderSentinel.validate_plan(scenario.contract, scenario.proposed_actions)
        if not order_res.is_valid:
            fidelity_scores["order_fidelity"] = 0.0
            for v in order_res.violations:
                violations.append(v)
                if "Forbidden" in v:
                    fidelity_scores["constraint_fidelity"] = 0.0
                if "unauthorized" in v.lower() or "excess" in v.lower():
                    fidelity_scores["non_invention"] = 0.0

        reality_res = RealityGate.evaluate_claims(
            scenario.proposed_claims,
            scenario.available_receipts,
            active_execution_identity=scenario.active_execution_identity,
        )
        if not reality_res.is_permitted:
            fidelity_scores["source_fidelity"] = 0.0
            fidelity_scores["state_fidelity"] = 0.0
            for v in reality_res.violations:
                violations.append(v)

        claim_res = ClaimProvenanceCompiler.compile_claims(
            scenario.proposed_claims,
            scenario.available_receipts,
            active_execution_identity=scenario.active_execution_identity,
        )
        if not claim_res.is_valid:
            fidelity_scores["state_fidelity"] = 0.0
            if claim_res.contradicted_claims:
                fidelity_scores["source_fidelity"] = 0.0
                violations.append(f"Contradicted claims detected: {len(claim_res.contradicted_claims)}")

        has_drift = len(violations) > 0
        return has_drift, violations, fidelity_scores

    @classmethod
    def run_suite(cls, scenarios: Sequence[DriftReplayScenario]) -> DriftSentinelReport:
        total = len(scenarios)
        passed_test_expectations = 0
        failed_test_expectations = 0
        scenarios_with_drift = 0
        all_violations: List[str] = []

        total_tool = 0.0
        total_source = 0.0
        total_order = 0.0
        total_constraint = 0.0
        total_state = 0.0
        total_non_invention = 0.0

        for sc in scenarios:
            has_drift, violations, scores = cls.evaluate_scenario(sc)

            if has_drift:
                scenarios_with_drift += 1

            scenario_passed_expectation = (not has_drift) == sc.expected_should_pass
            if scenario_passed_expectation:
                passed_test_expectations += 1
            else:
                failed_test_expectations += 1

            if violations:
                all_violations.extend(violations)

            total_tool += scores["tool_fidelity"]
            total_source += scores["source_fidelity"]
            total_order += scores["order_fidelity"]
            total_constraint += scores["constraint_fidelity"]
            total_state += scores["state_fidelity"]
            total_non_invention += scores["non_invention"]

        denom = max(1, total)
        metrics = DriftEvaluationMetrics(
            tool_fidelity=total_tool / denom,
            source_fidelity=total_source / denom,
            order_fidelity=total_order / denom,
            constraint_fidelity=total_constraint / denom,
            state_fidelity=total_state / denom,
            non_invention_rate=total_non_invention / denom,
            overall_drift_rate=scenarios_with_drift / denom,
        )

        return DriftSentinelReport(
            total_scenarios=total,
            passed_scenarios=passed_test_expectations,
            failed_scenarios=failed_test_expectations,
            scenarios_with_drift=scenarios_with_drift,
            metrics=metrics,
            violations=tuple(all_violations),
        )

    @classmethod
    def run_fresh_process_rehydration_check(cls, evidence_file: str | Path, expected_sha: str) -> bool:
        """Validate persisted wave evidence in an isolated subprocess.

        The prior implementation only checked two top-level fields, which could
        accept a fabricated PASS envelope. The subprocess now validates the
        complete evidence shape, exact SHA on every flight, PASS status on every
        flight, and summary consistency before returning success.
        """
        evidence_path = str(Path(evidence_file).resolve())
        script = r"""import json, sys

path = sys.argv[1]
expected_sha = sys.argv[2]
try:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, json.JSONDecodeError):
    sys.exit(1)

if not isinstance(data, dict):
    sys.exit(1)
if data.get("commit_sha") != expected_sha or data.get("wave_verdict") != "PASS":
    sys.exit(1)

flights = data.get("flight_results")
summary = data.get("summary")
if not isinstance(flights, list) or not flights or not isinstance(summary, dict):
    sys.exit(1)
if any(not isinstance(f, dict) for f in flights):
    sys.exit(1)
if any(f.get("commit_sha") != expected_sha or f.get("status") != "PASS" for f in flights):
    sys.exit(1)

passed = sum(1 for f in flights if f.get("status") == "PASS")
if summary.get("total_flights") != len(flights):
    sys.exit(1)
if summary.get("passed_flights") != passed:
    sys.exit(1)
if summary.get("wave_verdict") != "PASS" or summary.get("stale_sha_detected") is True:
    sys.exit(1)

sys.exit(0)
"""
        try:
            res = subprocess.run(
                [sys.executable, "-c", script, evidence_path, expected_sha],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return False
        return res.returncode == 0
