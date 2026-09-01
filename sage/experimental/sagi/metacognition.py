"""SAGI Metacognition & Decision Autopsy Engine.

Implements human decision functions for SAGI:
- Metacognitive Stack (Knowledge, Inference, Decision, Outcome Confidence, Risk Regulation)
- Decision Autopsy Engine (OUTCOME != DECISION QUALITY)
  - WIN + GOOD DECISION: Reinforce policy
  - WIN + BAD DECISION: Flag false success
  - LOSS + GOOD DECISION: Attribute to environmental variance / bad luck
  - LOSS + BAD DECISION: Flag genuine error
  - ENVIRONMENT_SHIFT, INFORMATION_SHOCK
- Counterfactual & Regret Memory Substrate
- Governed Operational Self-Model
"""

import enum
import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DecisionClassification(str, enum.Enum):
    """Classification of decision outcome vs decision quality."""
    WIN_GOOD_DECISION = "WIN_GOOD_DECISION"        # Reinforce policy
    WIN_BAD_DECISION = "WIN_BAD_DECISION"          # False success / lucky win
    LOSS_GOOD_DECISION = "LOSS_GOOD_DECISION"      # Variance / bad luck
    LOSS_BAD_DECISION = "LOSS_BAD_DECISION"        # Genuine error / policy flaw
    ENVIRONMENT_SHIFT = "ENVIRONMENT_SHIFT"        # Stale model / regime change
    INFORMATION_SHOCK = "INFORMATION_SHOCK"        # Invalidated by new external signal


class MetacognitiveState(BaseModel):
    """Stack representing self-monitoring and uncertainty awareness in SAGI."""
    knowledge_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    inference_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    decision_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    outcome_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    self_calibration_score: float = Field(default=0.85, ge=0.0, le=1.0)
    risk_regulation_factor: float = Field(default=1.0, ge=0.1, le=2.0)

    def compute_composite_confidence(self) -> float:
        """Compute composite metacognitive confidence across all layers."""
        weights = [0.2, 0.25, 0.3, 0.25]
        scores = [
            self.knowledge_confidence,
            self.inference_confidence,
            self.decision_confidence,
            self.outcome_confidence,
        ]
        return round(sum(w * s for w, s in zip(weights, scores)), 4)

    def calibrate(self, prediction_error: float) -> None:
        """Calibrate self-monitoring scores based on observed prediction error."""
        error = max(0.0, min(1.0, abs(prediction_error)))
        calibration_delta = (1.0 - error) - self.self_calibration_score
        self.self_calibration_score = max(0.1, min(1.0, round(self.self_calibration_score + 0.1 * calibration_delta, 4)))

        # Adjust risk regulation factor: higher prediction error increases risk regulation (more conservative)
        if error > 0.4:
            self.risk_regulation_factor = min(2.0, round(self.risk_regulation_factor * 1.15, 4))
        else:
            self.risk_regulation_factor = max(0.5, round(self.risk_regulation_factor * 0.95, 4))


class DecisionRegretRecord(BaseModel):
    """Record of counterfactual regret associated with a decision."""
    decision_id: str
    chosen_action: str
    actual_outcome_val: float
    counterfactual_outcomes: Dict[str, float] = Field(default_factory=dict)
    best_counterfactual_action: str = ""
    max_counterfactual_val: float = 0.0
    regret_score: float = 0.0
    timestamp: float = Field(default_factory=time.time)

    def compute_regret(self) -> float:
        """Calculate counterfactual regret: max(0, best_counterfactual - actual)."""
        if not self.counterfactual_outcomes:
            self.regret_score = 0.0
            return 0.0

        best_action, best_val = max(self.counterfactual_outcomes.items(), key=lambda item: item[1])
        self.best_counterfactual_action = best_action
        self.max_counterfactual_val = best_val
        self.regret_score = max(0.0, round(best_val - self.actual_outcome_val, 4))
        return self.regret_score


class DecisionAutopsy(BaseModel):
    """Structured record of a decision autopsy decoupling outcome from quality."""
    autopsy_id: str
    decision_id: str
    timestamp: float = Field(default_factory=time.time)
    chosen_action: str
    expected_outcome_val: float
    actual_outcome_val: float
    decision_quality_score: float = Field(ge=0.0, le=1.0) # 1.0 = optimal decision
    outcome_quality_score: float = Field(ge=0.0, le=1.0)  # 1.0 = positive outcome
    classification: DecisionClassification
    regret_record: Optional[DecisionRegretRecord] = None
    attribution: str
    lesson: str
    metacognitive_snapshot: MetacognitiveState


class SAGIDecisionAutopsyEngine:
    """Engine for performing structured decision autopsies and outcome attribution."""

    @staticmethod
    def perform_autopsy(
        decision_id: str,
        chosen_action: str,
        expected_outcome_val: float,
        actual_outcome_val: float,
        decision_quality_score: float,
        counterfactual_outcomes: Optional[Dict[str, float]] = None,
        metacognitive_state: Optional[MetacognitiveState] = None,
        environment_shifted: bool = False,
        information_shock: bool = False,
    ) -> DecisionAutopsy:
        """Perform a structured autopsy on a decision, enforcing OUTCOME != DECISION QUALITY."""
        m_state = metacognitive_state or MetacognitiveState()

        # Compute outcome quality score (normalized [0, 1])
        outcome_quality = max(0.0, min(1.0, round(actual_outcome_val, 4)))
        is_win = outcome_quality >= 0.5
        is_good_decision = decision_quality_score >= 0.6

        # Determine 4-quadrant / environmental classification
        if information_shock:
            classification = DecisionClassification.INFORMATION_SHOCK
            attribution = "Invalidated by sudden external signal / information shock"
            lesson = "Re-evaluate real-time signal monitoring and temporal locks"
        elif environment_shifted:
            classification = DecisionClassification.ENVIRONMENT_SHIFT
            attribution = "Regime change or environmental shift detected"
            lesson = "Update domain parameters and recalibrate baseline expectation"
        elif is_win and is_good_decision:
            classification = DecisionClassification.WIN_GOOD_DECISION
            attribution = "Solid decision policy with positive outcome"
            lesson = "Reinforce current decision policy and preserve weights"
        elif is_win and not is_good_decision:
            classification = DecisionClassification.WIN_BAD_DECISION
            attribution = "False success / lucky win despite poor decision policy"
            lesson = "Do not reinforce flawed policy; audit decision logic"
        elif not is_win and is_good_decision:
            classification = DecisionClassification.LOSS_GOOD_DECISION
            attribution = "Environmental variance or bad luck despite high decision quality"
            lesson = "Retain decision policy; adjust uncertainty/variance model"
        else:
            classification = DecisionClassification.LOSS_BAD_DECISION
            attribution = "Genuine error / flawed decision policy"
            lesson = "Modify decision parameters and record failure memory"

        # Compute counterfactual regret record
        regret_rec = None
        if counterfactual_outcomes:
            regret_rec = DecisionRegretRecord(
                decision_id=decision_id,
                chosen_action=chosen_action,
                actual_outcome_val=actual_outcome_val,
                counterfactual_outcomes=counterfactual_outcomes,
            )
            regret_rec.compute_regret()

        # Update metacognitive calibration based on prediction error
        pred_error = abs(expected_outcome_val - actual_outcome_val)
        m_state.calibrate(pred_error)

        autopsy_seed = f"{decision_id}:{time.time()}:{classification.value}"
        autopsy_id = f"autopsy_{hashlib.sha256(autopsy_seed.encode('utf-8')).hexdigest()[:12]}"

        return DecisionAutopsy(
            autopsy_id=autopsy_id,
            decision_id=decision_id,
            chosen_action=chosen_action,
            expected_outcome_val=expected_outcome_val,
            actual_outcome_val=actual_outcome_val,
            decision_quality_score=decision_quality_score,
            outcome_quality_score=outcome_quality,
            classification=classification,
            regret_record=regret_rec,
            attribution=attribution,
            lesson=lesson,
            metacognitive_snapshot=m_state,
        )


class SAGIOperationalSelfModel(BaseModel):
    """Governed self-model capturing current knowledge, uncertainties, assumptions, and lessons."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent_id: str = "SAGI_CORE_SELF_MODEL"
    metacognitive_state: MetacognitiveState = Field(default_factory=MetacognitiveState)
    active_assumptions: List[str] = Field(default_factory=list)
    recent_autopsies: List[DecisionAutopsy] = Field(default_factory=list)
    domain_reliability: Dict[str, float] = Field(default_factory=dict) # domain -> score [0, 1]
    total_autopsies_performed: int = 0

    def record_autopsy(self, autopsy: DecisionAutopsy, domain: str = "general") -> None:
        """Integrate a decision autopsy into the governed self-model."""
        self.recent_autopsies.append(autopsy)
        self.total_autopsies_performed += 1

        # Maintain max 50 recent autopsies
        if len(self.recent_autopsies) > 50:
            self.recent_autopsies.pop(0)

        # Update domain reliability based on decision quality (not raw outcome)
        current_rel = self.domain_reliability.get(domain, 0.8)
        new_rel = max(0.1, min(1.0, round(0.9 * current_rel + 0.1 * autopsy.decision_quality_score, 4)))
        self.domain_reliability[domain] = new_rel

        # Update self-model metacognition from autopsy snapshot
        self.metacognitive_state = autopsy.metacognitive_snapshot

    def get_governed_summary(self) -> Dict[str, Any]:
        """Return a structured summary of the self-model state."""
        return {
            "agent_id": self.agent_id,
            "composite_confidence": self.metacognitive_state.compute_composite_confidence(),
            "calibration_score": self.metacognitive_state.self_calibration_score,
            "risk_regulation_factor": self.metacognitive_state.risk_regulation_factor,
            "total_autopsies": self.total_autopsies_performed,
            "domain_reliability": self.domain_reliability,
            "active_assumptions_count": len(self.active_assumptions),
        }
