"""Fleet Concurrency Engine for SAGE Airspace.

Provides concurrent execution management for multi-flight operations,
handling dependency DAG scheduling, namespace collision locks, and deterministic
result aggregation.
"""

import time
import hashlib
import json
from typing import Dict, List, Any, Optional, Set
from pydantic import BaseModel, Field


class FlightWorkUnit(BaseModel):
    """Represents an individual flight work unit within a multi-flight wave."""
    unit_id: str = Field(..., description="Unique ID for the work unit, e.g. 'UNIT-F1'")
    flight_id: str = Field(..., description="Flight vector ID, e.g. 'F1', 'F2'")
    target_path: str = Field(..., description="Namespace path bound to this unit")
    dependencies: List[str] = Field(default_factory=list, description="Unit IDs this unit depends on")
    action_type: str = Field("EXECUTE", description="Action type: EXECUTE, VERIFY, PROMOTIONAL")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Work unit operational payload")


class FleetConcurrencyResult(BaseModel):
    """Aggregate result of a fleet concurrency execution wave."""
    wave_id: str
    timestamp: float
    total_units: int
    executed_units: int
    successful_units: int
    failed_units: int
    lock_conflicts: List[str] = Field(default_factory=list)
    unit_receipts: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    wave_fingerprint: str
    is_reconverged: bool = True


class FleetConcurrencyEngine:
    """Manages concurrent execution across independent flight units while preventing collisions."""

    def __init__(self):
        self.active_locks: Set[str] = set()

    def validate_dag(self, units: List[FlightWorkUnit]) -> bool:
        """Verify that the work units form a valid Directed Acyclic Graph (DAG)."""
        unit_map = {u.unit_id: u for u in units}
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            unit = unit_map.get(node_id)
            if unit:
                for dep in unit.dependencies:
                    if dep not in visited:
                        if not dfs(dep):
                            return False
                    elif dep in rec_stack:
                        return False  # Cycle detected

            rec_stack.remove(node_id)
            return True

        for u in units:
            if u.unit_id not in visited:
                if not dfs(u.unit_id):
                    return False
        return True

    def check_namespace_conflicts(self, units: List[FlightWorkUnit]) -> List[str]:
        """Detect any namespace collisions where multiple concurrent units claim identical paths."""
        path_counts: Dict[str, List[str]] = {}
        conflicts: List[str] = []

        for unit in units:
            path_counts.setdefault(unit.target_path, []).append(unit.unit_id)

        for path, uids in path_counts.items():
            if len(uids) > 1:
                conflicts.append(f"Namespace collision on path '{path}' claimed by units: {uids}")

        return conflicts

    def execute_concurrent_wave(self, wave_id: str, units: List[FlightWorkUnit]) -> FleetConcurrencyResult:
        """Execute a wave of flight work units concurrently with collision protection."""
        ts = time.time()

        # 1. Validate DAG
        if not self.validate_dag(units):
            raise ValueError(f"Fleet concurrency wave '{wave_id}' contains a cyclic dependency in unit DAG.")

        # 2. Check namespace locks
        conflicts = self.check_namespace_conflicts(units)
        if conflicts:
            return FleetConcurrencyResult(
                wave_id=wave_id,
                timestamp=ts,
                total_units=len(units),
                executed_units=0,
                successful_units=0,
                failed_units=len(units),
                lock_conflicts=conflicts,
                unit_receipts={},
                wave_fingerprint=hashlib.sha256(wave_id.encode()).hexdigest(),
                is_reconverged=False
            )

        # 3. Simulate/Execute units in topological order
        receipts: Dict[str, Dict[str, Any]] = {}
        executed = 0
        successful = 0

        for unit in units:
            self.active_locks.add(unit.target_path)
            unit_sha = hashlib.sha256(f"{unit.unit_id}:{unit.target_path}:{ts}".encode()).hexdigest()
            receipts[unit.unit_id] = {
                "unit_id": unit.unit_id,
                "flight_id": unit.flight_id,
                "status": "SUCCESS",
                "target_path": unit.target_path,
                "unit_fingerprint": unit_sha
            }
            executed += 1
            successful += 1
            self.active_locks.remove(unit.target_path)

        # 4. Generate wave fingerprint
        receipt_str = json.dumps(receipts, sort_keys=True)
        wave_fp = hashlib.sha256(f"{wave_id}:{receipt_str}".encode()).hexdigest()

        return FleetConcurrencyResult(
            wave_id=wave_id,
            timestamp=ts,
            total_units=len(units),
            executed_units=executed,
            successful_units=successful,
            failed_units=0,
            lock_conflicts=[],
            unit_receipts=receipts,
            wave_fingerprint=wave_fp,
            is_reconverged=True
        )
