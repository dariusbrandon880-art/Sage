"""C2 Wave Playbook Engine & Execution Pattern Optimizer."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlaybookExecutionReceipt(BaseModel):
    """Immutable receipt recording a multi-flight wave playbook execution."""

    playbook_id: str
    wave_id: str
    flight_frontiers: List[str] = Field(default_factory=list)
    success_rate: float
    first_pass_verification: bool
    execution_time_seconds: float
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 fingerprint for playbook execution receipt."""
        payload = {
            "playbook_id": self.playbook_id,
            "wave_id": self.wave_id,
            "flight_frontiers": sorted(self.flight_frontiers),
            "success_rate": self.success_rate,
            "first_pass_verification": self.first_pass_verification,
            "execution_time_seconds": self.execution_time_seconds,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class WaveOptimizationPattern(BaseModel):
    """Pattern containing recommended execution parameters for high-probability wave success."""

    pattern_name: str
    optimal_flight_count: int
    recommended_frontiers: List[str]
    historical_first_pass_rate: float
    confidence_score: float


class C2WavePlaybookEngine:
    """Records multi-flight wave executions, tracks first-pass verification rates, and suggests optimization patterns."""

    def __init__(self):
        self.receipts: List[PlaybookExecutionReceipt] = []

    def record_wave_execution(
        self,
        playbook_id: str,
        wave_id: str,
        flight_frontiers: List[str],
        success_rate: float,
        first_pass_verification: bool,
        execution_time_seconds: float,
    ) -> PlaybookExecutionReceipt:
        """Record execution metrics for a Big Jump Wave playbook."""
        receipt = PlaybookExecutionReceipt(
            playbook_id=playbook_id,
            wave_id=wave_id,
            flight_frontiers=flight_frontiers,
            success_rate=success_rate,
            first_pass_verification=first_pass_verification,
            execution_time_seconds=execution_time_seconds,
        )
        receipt.receipt_hash = receipt.compute_hash()
        self.receipts.append(receipt)
        return receipt

    def suggest_optimization_pattern(self) -> WaveOptimizationPattern:
        """Suggest an execution optimization pattern based on historical wave execution receipts."""
        if not self.receipts:
            return WaveOptimizationPattern(
                pattern_name="DEFAULT_FIVE_FLIGHT_WAVE",
                optimal_flight_count=5,
                recommended_frontiers=["F1", "F2", "F3", "F4", "F5"],
                historical_first_pass_rate=1.0,
                confidence_score=0.5,
            )

        total = len(self.receipts)
        first_pass_count = sum(1 for r in self.receipts if r.first_pass_verification)
        first_pass_rate = first_pass_count / total

        # Group frontiers by frequency
        frontier_counts: Dict[str, int] = {}
        for r in self.receipts:
            for f in r.flight_frontiers:
                frontier_counts[f] = frontier_counts.get(f, 0) + 1

        top_frontiers = sorted(frontier_counts.keys(), key=lambda k: frontier_counts[k], reverse=True)[:5]
        if len(top_frontiers) < 5:
            top_frontiers.extend([f"F{i}" for i in range(len(top_frontiers) + 1, 6)])

        return WaveOptimizationPattern(
            pattern_name="OPTIMIZED_PARALLEL_WAVE",
            optimal_flight_count=5,
            recommended_frontiers=top_frontiers,
            historical_first_pass_rate=first_pass_rate,
            confidence_score=min(1.0, 0.5 + (total * 0.1)),
        )
