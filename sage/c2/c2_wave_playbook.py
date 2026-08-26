"""C2 Wave Playbook Engine and execution-pattern optimizer."""

import hashlib
import json
import time
from typing import Dict, List
from pydantic import BaseModel, Field

class PlaybookExecutionReceipt(BaseModel):
    playbook_id: str
    wave_id: str
    flight_frontiers: List[str] = Field(default_factory=list)
    success_rate: float
    first_pass_verification: bool
    execution_time_seconds: float
    timestamp: float = Field(default_factory=time.time)
    receipt_hash: str = ""
    def compute_hash(self) -> str:
        payload = {"playbook_id": self.playbook_id, "wave_id": self.wave_id, "flight_frontiers": sorted(self.flight_frontiers), "success_rate": self.success_rate, "first_pass_verification": self.first_pass_verification, "execution_time_seconds": self.execution_time_seconds}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

class WaveOptimizationPattern(BaseModel):
    pattern_name: str
    optimal_flight_count: int
    recommended_frontiers: List[str]
    historical_first_pass_rate: float
    confidence_score: float

class C2WavePlaybookEngine:
    def __init__(self):
        self.receipts: List[PlaybookExecutionReceipt] = []
    def record_wave_execution(self, playbook_id: str, wave_id: str, flight_frontiers: List[str], success_rate: float, first_pass_verification: bool, execution_time_seconds: float) -> PlaybookExecutionReceipt:
        receipt = PlaybookExecutionReceipt(playbook_id=playbook_id, wave_id=wave_id, flight_frontiers=flight_frontiers, success_rate=success_rate, first_pass_verification=first_pass_verification, execution_time_seconds=execution_time_seconds)
        receipt.receipt_hash = receipt.compute_hash()
        self.receipts.append(receipt)
        return receipt
    def suggest_optimization_pattern(self) -> WaveOptimizationPattern:
        if not self.receipts:
            return WaveOptimizationPattern(pattern_name="DEFAULT_FIVE_FLIGHT_WAVE", optimal_flight_count=5, recommended_frontiers=["F1","F2","F3","F4","F5"], historical_first_pass_rate=1.0, confidence_score=0.5)
        total = len(self.receipts)
        first_pass_rate = sum(r.first_pass_verification for r in self.receipts) / total
        counts: Dict[str, int] = {}
        for receipt in self.receipts:
            for frontier in receipt.flight_frontiers:
                counts[frontier] = counts.get(frontier, 0) + 1
        top = sorted(counts, key=lambda key: counts[key], reverse=True)[:5]
        top.extend(f"F{i}" for i in range(len(top)+1, 6))
        return WaveOptimizationPattern(pattern_name="OPTIMIZED_PARALLEL_WAVE", optimal_flight_count=5, recommended_frontiers=top, historical_first_pass_rate=first_pass_rate, confidence_score=min(1.0, 0.5 + total * 0.1))
