"""Multi-Session Flight Collision Prevention & Lock Manager.

Manages namespace collision locks across concurrent multi-session Jules execution slots.
Enforces non-overlapping target boundaries and prevents duplicate work across parallel flights.
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


def normalize_path(path: str) -> str:
    """Normalizes path by stripping trailing slashes, dot segments, and leading slashes."""
    p = os.path.normpath(path.strip())
    if p == ".":
        return ""
    return p.replace("\\", "/")


def paths_overlap(path_a: str, path_b: str) -> bool:
    """Returns True if path_a and path_b are identical or one is a parent/child directory of the other."""
    norm_a = normalize_path(path_a)
    norm_b = normalize_path(path_b)

    if norm_a == norm_b:
        return True

    parts_a = [p for p in norm_a.split("/") if p]
    parts_b = [p for p in norm_b.split("/") if p]

    if not parts_a or not parts_b:
        return True

    min_len = min(len(parts_a), len(parts_b))
    return parts_a[:min_len] == parts_b[:min_len]


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
        # Map resource -> (session_id, flight_id)
        self._locked_resources: Dict[str, tuple[str, str]] = {}
        # Map (session_id, flight_id) -> set of resources
        self._session_locks: Dict[tuple[str, str], Set[str]] = {}

    def acquire_lock(self, request: FlightLockRequest) -> LockCheckResult:
        """Attempts to lock all resources for a flight request with hierarchical path containment checking."""
        requested_resources = set(request.target_files + request.target_namespaces)

        # Check for conflicts against all currently locked resources
        for req_res in requested_resources:
            for locked_res, (conflict_session, conflict_flight) in self._locked_resources.items():
                if (conflict_session, conflict_flight) != (request.session_id, request.flight_id):
                    if paths_overlap(req_res, locked_res):
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

        # Grant lock
        key = (request.session_id, request.flight_id)
        if key not in self._session_locks:
            self._session_locks[key] = set()

        for res in requested_resources:
            self._locked_resources[res] = key
            self._session_locks[key].add(res)

        res_result = LockCheckResult(
            acquired=True,
            session_id=request.session_id,
            flight_id=request.flight_id,
        )
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
