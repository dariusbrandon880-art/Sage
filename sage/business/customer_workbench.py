"""First-customer operating surface for the SAGE business product.

This module deliberately exposes the same governed state that C2 uses internally.
It does not create a second business workflow: it projects canonical mission,
identity, acceptance, evidence, and economic-measurement state for the customer.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sage.c2.mission_continuity import CANONICAL_MAIN_GOALS


@dataclass
class CustomerWorkflowMeasurement:
    """Outcome-level measurement for a completed customer workflow."""

    workflow_id: str
    completed: bool = False
    human_interventions: int = 0
    execution_seconds: float | None = None
    direct_cost_usd: float | None = None
    value_usd: float | None = None
    reusable_capability: str | None = None
    failure_count: int = 0
    recovery_count: int = 0
    evidence_refs: list[str] = field(default_factory=list)

    @property
    def net_value_usd(self) -> float | None:
        if self.value_usd is None or self.direct_cost_usd is None:
            return None
        return self.value_usd - self.direct_cost_usd


@dataclass
class CustomerWorkbenchSnapshot:
    """Customer-visible projection of governed SAGE operating state."""

    customer_id: str
    customer_role: str
    agent_identity: str
    engineering_identity: str
    intelligence_identity: str
    mission_id: str
    mission_goals: tuple[str, ...]
    active_flights: tuple[str, ...]
    acceptance_status: str
    deterministic_status: str
    empirical_status: str
    evidence_refs: tuple[str, ...]
    open_defects: tuple[str, ...]
    workflow_measurements: tuple[CustomerWorkflowMeasurement, ...]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["generated_at"] = self.generated_at
        data["mission_goals"] = list(self.mission_goals)
        data["active_flights"] = list(self.active_flights)
        data["evidence_refs"] = list(self.evidence_refs)
        data["open_defects"] = list(self.open_defects)
        data["workflow_measurements"] = [asdict(item) | {"net_value_usd": item.net_value_usd} for item in self.workflow_measurements]
        return data


class CustomerWorkbench:
    """Projects governed state without weakening any acceptance gate."""

    def __init__(self, customer_id: str = "SAGE_FIRST_CUSTOMER", measurement_path: str | Path = "evidence_capture/customer_workflows.jsonl"):
        self.customer_id = customer_id
        self.measurement_path = Path(measurement_path)
        self.measurements: list[CustomerWorkflowMeasurement] = []
        self._load_measurements()

    def _load_measurements(self) -> None:
        if not self.measurement_path.exists():
            return
        for line in self.measurement_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            self.measurements.append(CustomerWorkflowMeasurement(**payload))

    def _persist_measurement(self, measurement: CustomerWorkflowMeasurement) -> None:
        self.measurement_path.parent.mkdir(parents=True, exist_ok=True)
        with self.measurement_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(measurement), sort_keys=True) + "\n")

    def snapshot(self, acceptance_state: Any, active_flights: list[str] | tuple[str, ...]) -> CustomerWorkbenchSnapshot:
        return CustomerWorkbenchSnapshot(
            customer_id=self.customer_id,
            customer_role="FIRST_CUSTOMER",
            agent_identity="[SAGE::C2::CHATGPT]",
            engineering_identity="[SAGE::ENGINEER::JULES]",
            intelligence_identity="[SAGE::INTEL::GEMINI]",
            mission_id=acceptance_state.mission_id,
            mission_goals=tuple(CANONICAL_MAIN_GOALS),
            active_flights=tuple(active_flights),
            acceptance_status=acceptance_state.acceptance_status,
            deterministic_status=acceptance_state.deterministic_gate.status,
            empirical_status=acceptance_state.empirical_gate.status,
            evidence_refs=tuple(acceptance_state.evidence_refs),
            open_defects=tuple(acceptance_state.open_defects),
            workflow_measurements=tuple(self.measurements),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def record_workflow(self, measurement: CustomerWorkflowMeasurement) -> CustomerWorkflowMeasurement:
        if not measurement.workflow_id.strip():
            raise ValueError("workflow_id is required")
        if measurement.human_interventions < 0 or measurement.failure_count < 0 or measurement.recovery_count < 0:
            raise ValueError("workflow counters cannot be negative")
        self.measurements.append(measurement)
        self._persist_measurement(measurement)
        return measurement
