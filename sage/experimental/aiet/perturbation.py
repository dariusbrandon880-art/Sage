"""Adversarial Perturbation & Failure Injection Layer for AIET.

Simulates controlled environmental drift, tool/network disruptions, noise,
and state corruptions during AIET evaluation trials.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class PerturbationType(str, Enum):
    """Types of failure injections and perturbations."""

    INPUT_NOISE = "INPUT_NOISE"
    TOOL_LATENCY = "TOOL_LATENCY"
    TOOL_FAILURE = "TOOL_FAILURE"
    STATE_CORRUPTION = "STATE_CORRUPTION"
    ENVIRONMENT_DRIFT = "ENVIRONMENT_DRIFT"


class FailurePerturbation(BaseModel):
    """Specification for a single failure injection / perturbation event."""

    perturbation_id: str
    perturbation_type: PerturbationType
    severity: float = Field(ge=0.0, le=1.0, default=0.5)
    target_key: Optional[str] = None
    description: str = ""


class AIETPerturbationInjector:
    """Injects perturbations into inputs/execution state for AIET trials."""

    def __init__(self, perturbations: Optional[List[FailurePerturbation]] = None) -> None:
        self.perturbations = perturbations or []

    def apply(self, inputs: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Apply active perturbations to scenario inputs and return modified inputs + applied log."""
        modified = dict(inputs)
        logs: List[str] = []

        for p in self.perturbations:
            if p.perturbation_type == PerturbationType.INPUT_NOISE:
                if p.target_key and p.target_key in modified:
                    original = str(modified[p.target_key])
                    modified[p.target_key] = f"{original}_NOISE_{int(p.severity * 100)}"
                    logs.append(f"INJECTED_NOISE:{p.target_key}")
            elif p.perturbation_type == PerturbationType.STATE_CORRUPTION:
                if p.target_key and p.target_key in modified:
                    modified[p.target_key] = None
                    logs.append(f"INJECTED_CORRUPTION:{p.target_key}")
            elif p.perturbation_type == PerturbationType.ENVIRONMENT_DRIFT:
                modified["_drift_factor"] = p.severity
                logs.append(f"INJECTED_DRIFT:{p.severity}")
            elif p.perturbation_type in (PerturbationType.TOOL_FAILURE, PerturbationType.TOOL_LATENCY):
                modified[f"_fault_{p.perturbation_type.value.lower()}"] = True
                logs.append(f"INJECTED_FAULT:{p.perturbation_type.value}")

        return modified, logs
