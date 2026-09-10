"""SAGE Governed Continuity to Outcome & Benchmark Bridge.

Operationalizes the strategic frontier:
Governed continuity → measurable outcome improvement → external benchmark evidence

Strictly enforces the One-Way Import Law: as a module under sage/c2/, it
contains ZERO static imports from sage.experimental.* and resolves experimental
primitives dynamically via importlib.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import importlib
import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sage.c2.mission_continuity import (
    MissionContinuityFailure,
    MissionState,
    RehydrationSnapshot,
    require_canonical_main_goal_alignment,
)


def _get_git_head_sha() -> str:
    """Helper to resolve current 40-character Git HEAD commit SHA."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = res.stdout.strip()
        if len(sha) == 40:
            return sha
    except Exception:
        pass
    return "0000000000000000000000000000000000000000"


@dataclass(frozen=True)
class GovernedContinuityOutcomeReceipt:
    """Cryptographically bound receipt representing end-to-end strategic frontier evaluation."""

    receipt_id: str
    frontier_chain: str
    continuity_status: str
    continuity_checkpoint_hash: str
    outcome_verdict: str
    relative_success_gain: float
    recovery_rate: float
    regression_rate: float
    benchmark_classification: str
    benchmark_delta_score: float
    overall_frontier_verdict: str
    fail_closed_reasons: Tuple[str, ...] = field(default_factory=tuple)
    git_head_sha: str = field(default_factory=_get_git_head_sha)
    timestamp_utc: str = ""

    def canonical_payload(self) -> Dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "frontier_chain": self.frontier_chain,
            "continuity_status": self.continuity_status,
            "continuity_checkpoint_hash": self.continuity_checkpoint_hash,
            "outcome_verdict": self.outcome_verdict,
            "relative_success_gain": self.relative_success_gain,
            "recovery_rate": self.recovery_rate,
            "regression_rate": self.regression_rate,
            "benchmark_classification": self.benchmark_classification,
            "benchmark_delta_score": self.benchmark_delta_score,
            "overall_frontier_verdict": self.overall_frontier_verdict,
            "fail_closed_reasons": list(self.fail_closed_reasons),
            "git_head_sha": self.git_head_sha,
            "timestamp_utc": self.timestamp_utc,
        }

    def compute_hash(self) -> str:
        payload_str = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = self.canonical_payload()
        d["receipt_hash"] = self.compute_hash()
        return d


class GovernedContinuityOutcomeBridge:
    """Unified C2 Bridge for the strategic frontier chain:

    Governed continuity → measurable outcome improvement → external benchmark evidence
    """

    FRONTIER_CHAIN = "Governed continuity -> measurable outcome improvement -> external benchmark evidence"

    def __init__(self) -> None:
        # Dynamically load experimental modules to obey SAGE One-Way Import Law
        self._cc_mod = importlib.import_module("sage.experimental.act.continuity_control")
        self._lc_mod = importlib.import_module("sage.experimental.longitudinal_capability")
        self._p4_mod = importlib.import_module("sage.experimental.act.phase_4_eval")

    def execute_frontier_evaluation(
        self,
        main_goals: Tuple[str, ...],
        session_id: str,
        baseline_observations: Sequence[Any],
        sage_observations: Sequence[Any],
        evaluation_plan: Any,
        benchmark_baseline: Any,
        benchmark_intervention: Any,
        benchmark_observation: Any,
    ) -> GovernedContinuityOutcomeReceipt:
        """Execute all 3 stages of the strategic frontier in sequence."""
        fail_reasons: List[str] = []

        # STAGE 1: Governed Continuity
        continuity_status = "VERIFIED_INTACT"
        checkpoint_hash = ""
        try:
            require_canonical_main_goal_alignment(main_goals)
            snapshot = RehydrationSnapshot(
                mission=MissionState(
                    end_state="GOVERNED_CONTINUITY_VERIFIED",
                    main_goals=main_goals,
                )
            )
            # Instantiate dynamic SessionStateManager & CheckpointManager
            SessionStateManager = getattr(self._cc_mod, "SessionStateManager")
            CheckpointManager = getattr(self._cc_mod, "CheckpointManager")

            session_mgr = SessionStateManager(storage_path="sage_data/sessions_bridge_tmp")
            chk_mgr = CheckpointManager(storage_path="sage_data/checkpoints_bridge_tmp")

            session_state = session_mgr.create_session(
                session_id=session_id,
                active_objectives=list(main_goals),
            )
            checkpoint = chk_mgr.create_checkpoint(
                current_sage_state={"end_state": snapshot.mission.end_state},
                active_goals=list(main_goals),
                recent_decisions=["VERIFIED_CANONICAL_ALIGNMENT"],
                validation_status={"continuity_aligned": True},
            )

            rehydrated_session = session_mgr.retrieve_session(session_id)
            rehydrated_chk = chk_mgr.retrieve_checkpoint(checkpoint.id)

            if not rehydrated_session or not rehydrated_chk:
                continuity_status = "CONTINUITY_FAILURE"
                fail_reasons.append("SESSION_CHECKPOINT_REHYDRATION_FAILED")
            else:
                chk_json = json.dumps(
                    rehydrated_chk.model_dump(),
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                )
                checkpoint_hash = hashlib.sha256(chk_json.encode("utf-8")).hexdigest()
        except MissionContinuityFailure as mfe:
            continuity_status = "CONTINUITY_FAILURE"
            fail_reasons.append(f"MISSION_CONTINUITY_ALIGNMENT_FAILURE: {str(mfe)}")
        except Exception as e:
            continuity_status = "CONTINUITY_FAILURE"
            fail_reasons.append(f"GOVERNED_CONTINUITY_EXCEPTION: {str(e)}")

        # STAGE 2: Measurable Outcome Improvement
        outcome_verdict_str = "HOLD"
        relative_gain = 0.0
        recovery_rate = 0.0
        regression_rate = 1.0
        try:
            LongitudinalCapabilityEvaluator = getattr(
                self._lc_mod, "LongitudinalCapabilityEvaluator"
            )
            evaluator = LongitudinalCapabilityEvaluator(evaluation_plan)
            eval_receipt = evaluator.evaluate(baseline_observations, sage_observations)

            outcome_verdict_str = (
                eval_receipt.verdict.value
                if hasattr(eval_receipt.verdict, "value")
                else str(eval_receipt.verdict)
            )
            relative_gain = float(eval_receipt.relative_success_gain)
            recovery_rate = float(eval_receipt.recovery_rate)
            regression_rate = float(eval_receipt.regression_rate)

            if outcome_verdict_str != "PASS":
                fail_reasons.extend(
                    [f"OUTCOME_EVALUATION_{r}" for r in eval_receipt.fail_closed_reasons]
                )
        except Exception as e:
            outcome_verdict_str = "NEGATIVE_RESULT"
            fail_reasons.append(f"OUTCOME_IMPROVEMENT_EXCEPTION: {str(e)}")

        # STAGE 3: External Benchmark Evidence
        benchmark_class_str = "INVALID_EVALUATION"
        delta_score = 0.0
        try:
            PreRecordedPredictionValidator = getattr(
                self._p4_mod, "PreRecordedPredictionValidator"
            )
            validator_result = PreRecordedPredictionValidator.evaluate(
                benchmark_baseline,
                benchmark_intervention,
                benchmark_observation,
            )

            benchmark_class_str = (
                validator_result.classification.value
                if hasattr(validator_result.classification, "value")
                else str(validator_result.classification)
            )
            delta_score = float(validator_result.delta_score)

            if not validator_result.is_valid:
                fail_reasons.extend(
                    [f"BENCHMARK_VALIDATOR_{r}" for r in validator_result.rejection_reasons]
                )
            elif benchmark_class_str != "VALID_IMPROVEMENT":
                fail_reasons.append(f"BENCHMARK_NOT_IMPROVEMENT: {benchmark_class_str}")
        except Exception as e:
            benchmark_class_str = "INVALID_EVALUATION"
            fail_reasons.append(f"BENCHMARK_EVALUATION_EXCEPTION: {str(e)}")

        # OVERALL FRONTIER VERDICT
        if (
            continuity_status == "VERIFIED_INTACT"
            and outcome_verdict_str == "PASS"
            and benchmark_class_str == "VALID_IMPROVEMENT"
            and not fail_reasons
        ):
            overall_verdict = "PASS"
        elif any("REGRESSION" in r or "FAILURE" in r or "EXCEPTION" in r for r in fail_reasons):
            overall_verdict = "NEGATIVE_RESULT"
        else:
            overall_verdict = "HOLD"

        receipt_id = f"gco_rcpt_{hashlib.sha256(f'{session_id}:{time.time()}'.encode('utf-8')).hexdigest()[:12]}"
        timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return GovernedContinuityOutcomeReceipt(
            receipt_id=receipt_id,
            frontier_chain=self.FRONTIER_CHAIN,
            continuity_status=continuity_status,
            continuity_checkpoint_hash=checkpoint_hash,
            outcome_verdict=outcome_verdict_str,
            relative_success_gain=relative_gain,
            recovery_rate=recovery_rate,
            regression_rate=regression_rate,
            benchmark_classification=benchmark_class_str,
            benchmark_delta_score=delta_score,
            overall_frontier_verdict=overall_verdict,
            fail_closed_reasons=tuple(fail_reasons),
            timestamp_utc=timestamp_utc,
        )
