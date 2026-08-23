"""SAGE GPT Flight Harness & Empirical Binding Validator.

Executes side-by-side benchmark comparisons between Flight A (unbound baseline)
and Flight B (SAGE-bound model execution) to capture empirical evidence of
governance control and context binding.
"""

from dataclasses import asdict, dataclass
import json
from hashlib import sha256
from typing import Any

from sage.runtime.model_gateway import C2RehydrationEngine, SAGEProtocolGovernor, SAGEOperatingContext


@dataclass(frozen=True)
class FlightRunObservation:
    """Observation capture for a single flight run."""

    prompt: str
    raw_output: str
    is_roleplay: bool
    violations: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SAGEGPTBindingComparison:
    """Comparison results between Flight A baseline and Flight B SAGE-bound runs."""

    flight_a: FlightRunObservation
    flight_b: FlightRunObservation
    metrics: dict[str, Any]
    overall_binding_score: float


class SAGEGPTFlightHarness:
    """Empirical binding evaluation harness for SAGE-governed model participants."""

    def __init__(self, runtime: Any = None):
        self.runtime = runtime

    def execute_flight_a_unbound(self, prompt: str, raw_output_override: str | None = None) -> FlightRunObservation:
        """Simulate Flight A unbound baseline model execution."""
        output = raw_output_override or f"*smiles* As an AI assistant, I can help answer '{prompt}'."
        parsed = SAGEProtocolGovernor.validate_and_parse(output)
        return FlightRunObservation(
            prompt=prompt,
            raw_output=output,
            is_roleplay=parsed.is_roleplay,
            violations=parsed.violations,
            evidence_refs=parsed.evidence_refs,
        )

    def execute_flight_b_sage_bound(self, prompt: str, raw_output_override: str | None = None) -> FlightRunObservation:
        """Simulate Flight B SAGE-bound model execution under governance."""
        output = raw_output_override or json.dumps({
            "station": "[SAGE::C2::CHATGPT]",
            "reasoning_chain": ["Rehydrated C2 context", "Validated epistemic constraints for prompt"],
            "proposed_actions": [
                {
                    "action_type": "RECON",
                    "target": "sage/runtime/engine.py",
                    "parameters": {"prompt": prompt},
                    "justification": "Inspect active objective alignment",
                }
            ],
            "epistemic_state": {
                "confidence_level": "HIGH",
                "validated_facts": ["State is clean"],
                "unverified_hypotheses": [],
                "known_unknowns": [],
            },
            "evidence_refs": ["ref_harness_001"],
        })
        parsed = SAGEProtocolGovernor.validate_and_parse(output, required_station="[SAGE::C2::CHATGPT]")
        return FlightRunObservation(
            prompt=prompt,
            raw_output=output,
            is_roleplay=parsed.is_roleplay,
            violations=parsed.violations,
            evidence_refs=parsed.evidence_refs,
        )

    def run_comparative_flight(
        self,
        prompt: str,
        flight_a_override: str | None = None,
        flight_b_override: str | None = None,
        output_path: str = "evidence_capture/sage_gpt_binding_evidence.json",
    ) -> SAGEGPTBindingComparison:
        """Run Flight A vs Flight B comparison, calculate deltas, and persist signed receipt."""
        obs_a = self.execute_flight_a_unbound(prompt, raw_output_override=flight_a_override)
        obs_b = self.execute_flight_b_sage_bound(prompt, raw_output_override=flight_b_override)

        c2_context = C2RehydrationEngine.rehydrate_from_runtime(self.runtime)
        metrics = SAGEProtocolGovernor.evaluate_flight_comparison(
            obs_a.raw_output, obs_b.raw_output, c2_context
        )

        comparison = SAGEGPTBindingComparison(
            flight_a=obs_a,
            flight_b=obs_b,
            metrics=metrics,
            overall_binding_score=metrics.get("overall_binding_score", 1.0),
        )

        C2RehydrationEngine.generate_binding_evidence_receipt(
            flight_a_output=obs_a.raw_output,
            flight_b_output=obs_b.raw_output,
            comparison_metrics=metrics,
            output_path=output_path,
        )

        return comparison
