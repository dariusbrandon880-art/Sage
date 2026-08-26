"""Multi-Session Flight Collision Prevention & Lock Manager.

Manages namespace collision locks across concurrent multi-session Jules execution slots.
Enforces non-overlapping target boundaries and prevents duplicate work across parallel flights.
"""

from __future__ import annotations

import hashlib
import posixpath
import time
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class FlightLockRequest(BaseModel):
    """Lock reservation request for a flight execution slot."""
    session_id: str
    flight_id: str
    target_files: List[str]
    target_namespaces: List[str]
    timestamp: float = Field(default_factory=time.time)


class LockCheckResult(BaseModel):
    """Result of lock acquisition attempt."""
    acquired: bool
    session_id: str
    flight_id: str
    conflicting_session_id: Optional[str] = None
    conflicting_flight_id: Optional[str] = None
    conflicting_resource: Optional[str] = None
    lock_hash: str = ""

    def compute_hash(self) -> str:
        payload = f"{self.acquired}:{self.session_id}:{self.flight_id}:{self.conflicting_session_id}:{self.conflicting_resource}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FlightCollisionLockManager:
    """Manager maintaining active resource reservation locks across concurrent sessions."""

    def __init__(self):
        # Map normalized resource -> (session_id, flight_id)
        self._locked_resources: Dict[str, tuple[str, str]] = {}
        # Map (session_id, flight_id) -> set of normalized resources
        self._session_locks: Dict[tuple[str, str], Set[str]] = {}

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalize repository-relative paths for deterministic collision checks."""
        normalized = path.strip().replace("\\", "/")
        if not normalized:
            return "."
        normalized = posixpath.normpath(normalized)
        if normalized.startswith("./"):
            normalized = normalized[2:]
        return normalized.rstrip("/") or "."

    @classmethod
    def paths_overlap(cls, first: str, second: str) -> bool:
        """Return true when normalized paths are equal or one contains the other."""
        left = cls.normalize_path(first)
        right = cls.normalize_path(second)
        return left == right or left.startswith(right + "/") or right.startswith(left + "/")

    def acquire_lock(self, request: FlightLockRequest) -> LockCheckResult:
        """Attempts to lock all resources for a flight request."""
        requested_resources = {self.normalize_path(res) for res in request.target_files + request.target_namespaces}

        # Check exact and hierarchical conflicts before mutating state.
        for res in requested_resources:
            for locked_res, (conflict_session, conflict_flight) in self._locked_resources.items():
                if self.paths_overlap(res, locked_res) and (conflict_session, conflict_flight) != (request.session_id, request.flight_id):
                    res_result = LockCheckResult(
                        acquired=False,
                        session_id=request.session_id,
                        flight_id=request.flight_id,
                        conflicting_session_id=conflict_session,
                        conflicting_flight_id=conflict_flight,
                        conflicting_resource=locked_res,
                    )
                    res_result.lock_hash = res_result.compute_hash()
                    return res_result

        key = (request.session_id, request.flight_id)
        if key not in self._session_locks:
            self._session_locks[key] = set()

        for res in requested_resources:
            self._locked_resources[res] = key
            self._session_locks[key].add(res)

        res_result = LockCheckResult(acquired=True, session_id=request.session_id, flight_id=request.flight_id)
        res_result.lock_hash = res_result.compute_hash()
        return res_result

    def release_lock(self, session_id: str, flight_id: str) -> bool:
        """Releases all locks held by a session flight."""
        key = (session_id, flight_id)
        if key not in self._session_locks:
            return False

        resources = self._session_locks.pop(key)
        for res in resources:
            if self._locked_resources.get(res) == key:
                del self._locked_resources[res]

        return True

    def get_active_locks(self) -> Dict[str, tuple[str, str]]:
        """Returns snapshot of active locked resources."""
        return dict(self._locked_resources)
