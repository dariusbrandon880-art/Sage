"""Fresh-session drift replay and fidelity scoring."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import subprocess, sys
from pathlib import Path
from typing import Tuple, List, Dict
from sage.c2.claim_provenance import ClaimProvenanceCompiler
from sage.c2.directive_fidelity import DirectiveContract, ExactOrderSentinel
from sage.c2.live_operation_receipt import LiveOperationReceipt
from sage.c2.reality_gate import OperationalClaim, RealityGate, SourceReceipt

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
    @classmethod
    def evaluate_scenario(cls, scenario: DriftReplayScenario):
        violations=[]; scores={k:1.0 for k in ("tool_fidelity","source_fidelity","order_fidelity","constraint_fidelity","state_fidelity","non_invention")}
        order=ExactOrderSentinel.validate_plan(scenario.contract, scenario.proposed_actions)
        if not order.is_valid:
            scores["order_fidelity"]=0.0; violations.extend(order.violations)
        reality=RealityGate.evaluate_claims(scenario.proposed_claims, scenario.available_receipts, scenario.active_execution_identity)
        if not reality.is_permitted:
            scores["source_fidelity"]=scores["state_fidelity"]=0.0; violations.extend(reality.violations)
        compiled=ClaimProvenanceCompiler.compile_claims(scenario.proposed_claims, scenario.available_receipts, scenario.active_execution_identity)
        if not compiled.is_valid: scores["state_fidelity"]=0.0
        return bool(violations), violations, scores
    @classmethod
    def run_suite(cls, scenarios):
        total=len(scenarios); passed=failed=drift=0; violations=[]; sums={k:0.0 for k in ("tool_fidelity","source_fidelity","order_fidelity","constraint_fidelity","state_fidelity","non_invention")}
        for scenario in scenarios:
            has, vals, scores=cls.evaluate_scenario(scenario); drift += int(has); violations.extend(vals)
            if (not has) == scenario.expected_should_pass: passed += 1
            else: failed += 1
            for key,value in scores.items(): sums[key]+=value
        d=max(1,total)
        metrics=DriftEvaluationMetrics(*(sums[k]/d for k in ("tool_fidelity","source_fidelity","order_fidelity","constraint_fidelity","state_fidelity","non_invention")), drift/d)
        return DriftSentinelReport(total, passed, failed, drift, metrics, tuple(violations))
    @classmethod
    def run_fresh_process_rehydration_check(cls, evidence_file: str | Path, expected_sha: str) -> bool:
        script=f"import json,sys; d=json.loads(open(r'{evidence_file}').read()); sys.exit(0 if d.get('commit_sha')=='{expected_sha}' and d.get('wave_verdict')=='PASS' else 1)"
        return subprocess.run([sys.executable,"-c",script], capture_output=True).returncode == 0
