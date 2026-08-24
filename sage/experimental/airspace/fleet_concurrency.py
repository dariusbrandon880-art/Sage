"""Fleet concurrency substrate for bounded SAGE flight waves.

The engine coordinates independent work units without granting C2 authority. It
validates dependency structure, rejects namespace collisions before execution,
executes independent DAG levels concurrently, and emits deterministic receipts.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import threading
import time
from typing import Any, Dict, List, Set

from pydantic import BaseModel, Field


class FlightWorkUnit(BaseModel):
    """One bounded work unit in a multi-flight wave."""

    unit_id: str = Field(..., description="Unique work-unit identifier")
    flight_id: str = Field(..., description="Independent flight vector identifier")
    target_path: str = Field(..., description="Repository namespace claimed by the unit")
    dependencies: List[str] = Field(default_factory=list, description="Unit IDs that must complete first")
    action_type: str = Field("EXECUTE", description="Bounded action classification")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Non-authorizing work payload")


class FleetConcurrencyResult(BaseModel):
    """Immutable-style aggregate result for one fleet wave."""

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
    """Coordinate independent flight units while preserving bounded authority."""

    _ALLOWED_ACTION_TYPES = {"EXECUTE", "VERIFY"}

    def __init__(self) -> None:
        self.active_locks: Set[str] = set()
        self._lock_guard = threading.Lock()

    def _validate_units(self, units: List[FlightWorkUnit]) -> Dict[str, FlightWorkUnit]:
        unit_map = {unit.unit_id: unit for unit in units}
        if len(unit_map) != len(units):
            raise ValueError("Fleet concurrency wave contains duplicate unit IDs.")
        for unit in units:
            if unit.action_type not in self._ALLOWED_ACTION_TYPES:
                raise ValueError(
                    f"Unsupported action type '{unit.action_type}' for bounded fleet execution."
                )
            missing = [dep for dep in unit.dependencies if dep not in unit_map]
            if missing:
                raise ValueError(
                    f"Fleet concurrency wave contains unknown dependencies for '{unit.unit_id}': {missing}"
                )
        return unit_map

    def validate_dag(self, units: List[FlightWorkUnit]) -> bool:
        """Return true only when unit IDs, dependencies, and cycles are valid."""
        unit_map = self._validate_units(units)
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(node_id: str) -> bool:
            if node_id in visiting:
                return False
            if node_id in visited:
                return True
            visiting.add(node_id)
            for dep in unit_map[node_id].dependencies:
                if not dfs(dep):
                    return False
            visiting.remove(node_id)
            visited.add(node_id)
            return True

        return all(dfs(unit_id) for unit_id in unit_map)

    def _execution_levels(self, units: List[FlightWorkUnit]) -> List[List[FlightWorkUnit]]:
        unit_map = {unit.unit_id: unit for unit in units}
        remaining = {unit.unit_id: set(unit.dependencies) for unit in units}
        levels: List[List[FlightWorkUnit]] = []

        while remaining:
            ready_ids = sorted(unit_id for unit_id, deps in remaining.items() if not deps)
            if not ready_ids:
                raise ValueError("Fleet concurrency wave contains a cyclic dependency in unit DAG.")
            levels.append([unit_map[unit_id] for unit_id in ready_ids])
            for unit_id in ready_ids:
                remaining.pop(unit_id)
            for deps in remaining.values():
                deps.difference_update(ready_ids)
        return levels

    def check_namespace_conflicts(self, units: List[FlightWorkUnit]) -> List[str]:
        """Detect duplicate repository namespace claims before any unit executes."""
        path_counts: Dict[str, List[str]] = {}
        for unit in units:
            path_counts.setdefault(unit.target_path, []).append(unit.unit_id)
        return [
            f"Namespace collision on path '{path}' claimed by units: {uids}"
            for path, uids in sorted(path_counts.items())
            if len(uids) > 1
        ]

    @staticmethod
    def _unit_receipt(unit: FlightWorkUnit) -> Dict[str, Any]:
        canonical = {
            "action_type": unit.action_type,
            "dependencies": sorted(unit.dependencies),
            "flight_id": unit.flight_id,
            "payload": unit.payload,
            "target_path": unit.target_path,
            "unit_id": unit.unit_id,
        }
        fingerprint = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return {
            "unit_id": unit.unit_id,
            "flight_id": unit.flight_id,
            "status": "SUCCESS",
            "target_path": unit.target_path,
            "unit_fingerprint": fingerprint,
        }

    def _execute_unit(self, unit: FlightWorkUnit) -> Dict[str, Any]:
        with self._lock_guard:
            if unit.target_path in self.active_locks:
                raise RuntimeError(f"Namespace lock conflict on '{unit.target_path}'.")
            self.active_locks.add(unit.target_path)
        try:
            return self._unit_receipt(unit)
        finally:
            with self._lock_guard:
                self.active_locks.remove(unit.target_path)

    def execute_concurrent_wave(self, wave_id: str, units: List[FlightWorkUnit]) -> FleetConcurrencyResult:
        """Execute dependency-ready units concurrently and reconverge their receipts."""
        timestamp = time.time()
        unit_map = self._validate_units(units)
        if not self.validate_dag(units):
            raise ValueError(f"Fleet concurrency wave '{wave_id}' contains a cyclic dependency in unit DAG.")

        conflicts = self.check_namespace_conflicts(units)
        if conflicts:
            fingerprint = hashlib.sha256(
                json.dumps({"wave_id": wave_id, "conflicts": conflicts}, sort_keys=True).encode()
            ).hexdigest()
            return FleetConcurrencyResult(
                wave_id=wave_id,
                timestamp=timestamp,
                total_units=len(units),
                executed_units=0,
                successful_units=0,
                failed_units=len(units),
                lock_conflicts=conflicts,
                wave_fingerprint=fingerprint,
                is_reconverged=False,
            )

        receipts: Dict[str, Dict[str, Any]] = {}
        for level in self._execution_levels(list(unit_map.values())):
            with ThreadPoolExecutor(max_workers=len(level)) as executor:
                results = list(executor.map(self._execute_unit, level))
            receipts.update({receipt["unit_id"]: receipt for receipt in results})

        canonical_receipts = {key: receipts[key] for key in sorted(receipts)}
        wave_payload = {"wave_id": wave_id, "unit_receipts": canonical_receipts}
        wave_fingerprint = hashlib.sha256(
            json.dumps(wave_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        return FleetConcurrencyResult(
            wave_id=wave_id,
            timestamp=timestamp,
            total_units=len(units),
            executed_units=len(receipts),
            successful_units=len(receipts),
            failed_units=0,
            lock_conflicts=[],
            unit_receipts=canonical_receipts,
            wave_fingerprint=wave_fingerprint,
            is_reconverged=True,
        )
