"""SAGE C2 Wave Playbook & Capability Growth Engine.

Enables ChatGPT C2 to continuously learn and compound multi-flight execution playbooks
from verified historical evidence receipts. Optimizes task decomposition, collision avoidance,
concurrency throughput, and first-pass verification rates across parallel execution flights.
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Sequence
from pydantic import BaseModel, Field


class WaveOptimizationPattern(BaseModel):
    """Schema for a verified multi-flight execution playbook pattern."""

    pattern_id: str
    name: str
    description: str
    target_frontiers: list[str] = Field(default_factory=list)
    namespace_isolation_rules: list[str] = Field(default_factory=list)
    recommended_concurrency: int = Field(default=5, ge=1, le=20)
    historical_first_pass_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    timestamp: float = Field(default_factory=time.time)

    def digest(self) -> str:
        payload = {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "target_frontiers": sorted(self.target_frontiers),
            "namespace_isolation_rules": sorted(self.namespace_isolation_rules),
            "recommended_concurrency": self.recommended_concurrency,
            "historical_first_pass_rate": self.historical_first_pass_rate,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class PlaybookExecutionReceipt(BaseModel):
    """Immutable receipt generated when C2 applies a wave playbook pattern."""

    receipt_id: str
    pattern_id: str
    wave_id: str
    flights_executed: int
    zero_collision_verified: bool
    first_pass_success: bool
    performance_delta: dict[str, Any] = Field(default_factory=dict)
    receipt_digest: str = ""
    timestamp: float = Field(default_factory=time.time)


class C2WavePlaybookEngine:
    """Engine storing, retrieving, and compounding multi-flight execution playbooks."""

    def __init__(self):
        self.patterns: dict[str, WaveOptimizationPattern] = {}
        self.execution_receipts: list[PlaybookExecutionReceipt] = []

    def register_pattern(self, pattern: WaveOptimizationPattern) -> str:
        """Register a verified multi-flight optimization pattern."""
        if not pattern.pattern_id.strip():
            raise ValueError("pattern_id is required")
        self.patterns[pattern.pattern_id] = pattern
        return pattern.digest()

    def find_matching_patterns(self, frontiers: Sequence[str]) -> list[WaveOptimizationPattern]:
        """Find playbooks matching requested target frontiers, sorted by first-pass rate."""
        requested_set = set(str(f).strip() for f in frontiers)
        matches = []
        for p in self.patterns.values():
            if any(f in requested_set for f in p.target_frontiers):
                matches.append(p)

        return sorted(matches, key=lambda p: (-p.historical_first_pass_rate, p.pattern_id))

    def record_wave_execution(
        self,
        pattern_id: str,
        wave_id: str,
        flights_executed: int,
        zero_collision: bool,
        first_pass_success: bool,
    ) -> PlaybookExecutionReceipt:
        """Record execution outcome, updating pattern metrics and persisting an immutable receipt."""
        if pattern_id not in self.patterns:
            raise ValueError(f"Unknown pattern_id: {pattern_id}")

        pattern = self.patterns[pattern_id]

        # Update historical first-pass rate moving average combining baseline prior
        runs_for_pattern = [r for r in self.execution_receipts if r.pattern_id == pattern_id]
        total_runs = len(runs_for_pattern) + 1
        current_rate = pattern.historical_first_pass_rate
        outcome_val = 1.0 if first_pass_success else 0.0
        new_rate = (current_rate + outcome_val) / 2.0
        updated_pattern = pattern.model_copy(update={"historical_first_pass_rate": round(new_rate, 4)})
        self.patterns[pattern_id] = updated_pattern

        rec_id = f"pb-rec-{int(time.time() * 1000)}"
        raw_payload = {
            "receipt_id": rec_id,
            "pattern_id": pattern_id,
            "wave_id": wave_id,
            "flights_executed": flights_executed,
            "zero_collision": zero_collision,
            "first_pass_success": first_pass_success,
        }
        digest = hashlib.sha256(json.dumps(raw_payload, sort_keys=True).encode("utf-8")).hexdigest()

        receipt = PlaybookExecutionReceipt(
            receipt_id=rec_id,
            pattern_id=pattern_id,
            wave_id=wave_id,
            flights_executed=flights_executed,
            zero_collision_verified=zero_collision,
            first_pass_success=first_pass_success,
            performance_delta={
                "previous_first_pass_rate": pattern.historical_first_pass_rate,
                "updated_first_pass_rate": updated_pattern.historical_first_pass_rate,
                "total_runs_evaluated": total_runs,
            },
            receipt_digest=digest,
        )
        self.execution_receipts.append(receipt)
        return receipt
