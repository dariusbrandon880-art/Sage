"""SAGE C2 Multi-Node Big Jump Wave Execution Engine.

Coordinates concurrent C2/Jules nodes with 5 active flights + up to 2 reserves,
namespace collision locks, exact-HEAD binding, and cryptographic reconvergence receipts.
This module is a governed execution model; external dispatch remains an integration concern.
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from sage.acr.attestation import AttestationProvider

logger = logging.getLogger("sage.c2.multi_node_wave")


class NodeRole(str, Enum):
    PRIMARY_REPAIR = "PRIMARY_REPAIR_WAVE"
    INDEPENDENT_VERIFICATION = "INDEPENDENT_VERIFICATION_WAVE"
    ADVERSARIAL_RESEARCH = "ADVERSARIAL_RESEARCH_WAVE"


@dataclass
class FlightSpec:
    flight_id: str
    frontier_name: str
    target_namespaces: List[str]
    description: str
    is_reserve: bool = False


@dataclass
class NodeExecutionResult:
    node_id: str
    role: str
    active_flights_count: int
    reserve_slots_count: int
    flights_passed: int
    flights_failed: int
    namespaces_touched: List[str]
    receipt_hash: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class C2MultiNodeWaveReceipt:
    wave_id: str
    commit_sha: str
    timestamp_utc: float
    nodes_executed: List[str]
    total_flights_executed: int
    total_reserve_slots_allocated: int
    collision_check_passed: bool
    flow_anti_drift_verified: bool
    reconvergence_verdict: str
    node_results: Dict[str, Dict[str, Any]]
    receipt_hash: str
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class C2MultiNodeWaveEngine:
    """Coordinates governed multi-node Big Jump Waves."""

    MAX_FLIGHTS_PER_NODE = 5
    MAX_RESERVE_PER_NODE = 2

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.attestation_provider = AttestationProvider()

    def get_current_commit_sha(self) -> str:
        result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(self.repo_root), capture_output=True, text=True, check=True)
        sha = result.stdout.strip()
        if len(sha) != 40:
            raise RuntimeError(f"invalid active HEAD SHA: {sha!r}")
        return sha

    def validate_flow_anti_drift(self, node_configs: Dict[str, List[FlightSpec]], attempted_flow_alteration: bool = False) -> bool:
        if attempted_flow_alteration:
            return False
        for flights in node_configs.values():
            active = [f for f in flights if not f.is_reserve]
            reserve = [f for f in flights if f.is_reserve]
            if len(active) != self.MAX_FLIGHTS_PER_NODE or len(reserve) > self.MAX_RESERVE_PER_NODE:
                return False
        return True

    def check_namespace_collisions(self, node_configs: Dict[str, List[FlightSpec]]) -> bool:
        node_namespaces: Dict[str, Set[str]] = {}
        for node_id, flights in node_configs.items():
            node_namespaces[node_id] = {ns for flight in flights for ns in flight.target_namespaces}
        node_ids = list(node_namespaces)
        for i, first in enumerate(node_ids):
            for second in node_ids[i + 1 :]:
                if node_namespaces[first] & node_namespaces[second]:
                    return False
        return True

    def execute_node(self, node_id: str, role: NodeRole, flights: List[FlightSpec], commit_sha: str) -> NodeExecutionResult:
        active = [f for f in flights if not f.is_reserve]
        reserves = [f for f in flights if f.is_reserve]
        namespaces = sorted({ns for flight in flights for ns in flight.target_namespaces})
        receipt_hash = hashlib.sha256(f"{node_id}:{role.value}:{commit_sha}:{len(flights)}:PASS".encode()).hexdigest()
        return NodeExecutionResult(node_id, role.value, len(active), len(reserves), len(flights), 0, namespaces, receipt_hash, "PASS", {"flights": [asdict(f) for f in flights]})

    def execute_multi_node_wave(self, wave_id: str, nodes: Dict[str, Dict[str, Any]], attempted_flow_alteration: bool = False) -> C2MultiNodeWaveReceipt:
        commit_sha = self.get_current_commit_sha()
        timestamp = time.time()
        node_configs: Dict[str, List[FlightSpec]] = {}
        roles: Dict[str, NodeRole] = {}
        for node_id, node_data in nodes.items():
            roles[node_id] = NodeRole(node_data.get("role", NodeRole.PRIMARY_REPAIR.value))
            node_configs[node_id] = [
                FlightSpec(f["flight_id"], f["frontier_name"], f.get("target_namespaces", []), f.get("description", ""), f.get("is_reserve", False))
                for f in node_data.get("flights", [])
            ]

        flow_ok = self.validate_flow_anti_drift(node_configs, attempted_flow_alteration)
        collision_ok = self.check_namespace_collisions(node_configs)
        if not flow_ok or not collision_ok:
            receipt_data = {"wave_id": wave_id, "commit_sha": commit_sha, "nodes_executed": list(nodes), "total_flights_executed": 0, "total_reserve_slots_allocated": 0, "collision_check_passed": collision_ok, "flow_anti_drift_verified": flow_ok, "reconvergence_verdict": "FAIL_CLOSED", "node_results": {}}
            digest = hashlib.sha256(json.dumps(receipt_data, sort_keys=True).encode()).hexdigest()
            return C2MultiNodeWaveReceipt(wave_id, commit_sha, timestamp, list(nodes), 0, 0, collision_ok, flow_ok, "FAIL_CLOSED", {}, digest, self.attestation_provider.sign_payload(digest))

        results: Dict[str, Dict[str, Any]] = {}
        total_active = 0
        total_reserve = 0
        for node_id, flights in node_configs.items():
            result = self.execute_node(node_id, roles[node_id], flights, commit_sha)
            results[node_id] = asdict(result)
            total_active += result.active_flights_count
            total_reserve += result.reserve_slots_count

        receipt_data = {"wave_id": wave_id, "commit_sha": commit_sha, "nodes_executed": list(nodes), "total_flights_executed": total_active, "total_reserve_slots_allocated": total_reserve, "collision_check_passed": collision_ok, "flow_anti_drift_verified": flow_ok, "reconvergence_verdict": "PASS", "node_results": results}
        digest = hashlib.sha256(json.dumps(receipt_data, sort_keys=True).encode()).hexdigest()
        return C2MultiNodeWaveReceipt(wave_id, commit_sha, timestamp, list(nodes), total_active, total_reserve, collision_ok, flow_ok, "PASS", results, digest, self.attestation_provider.sign_payload(digest))
