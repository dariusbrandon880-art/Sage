"""SAGE Organism & Jigsaw Architecture Convergence Engine.

This module enforces the 'One Organism, Modular Organs' architecture and the Jigsaw Taxonomy.
It registers subsystem relationships (CORE, SERVICE, PROJECTION, EVIDENCE_LEARNING),
verifies single-source-of-truth authority boundaries, performs dynamic on-disk module
existence checks, and evaluates the 10 Connective Tissue Integration Gates with live verification.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class JigsawRelationship(str, Enum):
    """Canonical subsystem relationships within the SAGE Organism."""

    CORE = "CORE"
    SERVICE = "SERVICE"
    PROJECTION = "PROJECTION"
    EVIDENCE_LEARNING = "EVIDENCE_LEARNING"


class SubsystemRegistration(BaseModel):
    """Registration record mapping a SAGE subsystem to its Jigsaw relationship."""

    subsystem_id: str
    module_path: str
    relationship: JigsawRelationship
    description: str
    authoritative_domain: str | None = None


class ConnectiveTissueGate(BaseModel):
    """Execution receipt for one of the 10 Organism Connective Tissue Integration Gates."""

    gate_id: str
    gate_name: str
    source_organ: str
    target_organ: str
    passed: bool
    evidence_ref: str
    details: dict[str, Any] = Field(default_factory=dict)


class OrganismVerificationReceipt(BaseModel):
    """Immutable SHA-256 evidence receipt for full organism integration verification."""

    receipt_id: str
    commit_sha: str
    subsystem_count: int
    duplicate_authorities_detected: int
    gates_evaluated: int
    gates_passed: int
    all_gates_passed: bool
    receipt_hash: str
    subsystems: list[SubsystemRegistration]
    gate_results: list[ConnectiveTissueGate]

    def verify(self) -> bool:
        """Verify the cryptographic integrity of the organism verification receipt."""
        if len(self.commit_sha) != 40:
            return False
        computed_hash = _compute_receipt_hash(
            receipt_id=self.receipt_id,
            commit_sha=self.commit_sha,
            subsystem_count=self.subsystem_count,
            duplicate_authorities_detected=self.duplicate_authorities_detected,
            gates_evaluated=self.gates_evaluated,
            gates_passed=self.gates_passed,
            all_gates_passed=self.all_gates_passed,
            subsystems=[s.model_dump() for s in self.subsystems],
            gate_results=[g.model_dump() for g in self.gate_results],
        )
        return computed_hash == self.receipt_hash


def get_canonical_subsystem_catalog() -> list[SubsystemRegistration]:
    """Retrieve the authoritative catalog of SAGE subsystems mapped to Jigsaw taxonomy."""
    return [
        SubsystemRegistration(
            subsystem_id="sage_runtime",
            module_path="sage/runtime/engine.py",
            relationship=JigsawRelationship.CORE,
            description="Core execution runtime & state manager",
            authoritative_domain="state_authority",
        ),
        SubsystemRegistration(
            subsystem_id="c2_mission_control",
            module_path="sage/c2/",
            relationship=JigsawRelationship.CORE,
            description="Command & Control coordination surface",
            authoritative_domain="c2_authority",
        ),
        SubsystemRegistration(
            subsystem_id="frontier_admission",
            module_path="sage/c2/frontier_admission.py",
            relationship=JigsawRelationship.CORE,
            description="Frontier admission and protected namespace checking",
            authoritative_domain="frontier_admission",
        ),
        SubsystemRegistration(
            subsystem_id="frontier_intelligence_bridge",
            module_path="sage/c2/frontier_intelligence_bridge.py",
            relationship=JigsawRelationship.CORE,
            description="Frontier intelligence bridge and mission plan synthesis",
        ),
        SubsystemRegistration(
            subsystem_id="multi_frontier_dispatch",
            module_path="sage/c2/multi_frontier_dispatch.py",
            relationship=JigsawRelationship.CORE,
            description="Multi-frontier dispatcher for parallel flight execution",
        ),
        SubsystemRegistration(
            subsystem_id="chatgpt_c2_contract",
            module_path="sage/c2/chatgpt_c2_contract.py",
            relationship=JigsawRelationship.CORE,
            description="ChatGPT C2 governance contract and operational protocol",
        ),
        SubsystemRegistration(
            subsystem_id="sagi_metacognition",
            module_path="sage/experimental/sagi/metacognition.py",
            relationship=JigsawRelationship.CORE,
            description="SAGI metacognition, decision autopsy, and self-model",
        ),
        SubsystemRegistration(
            subsystem_id="super_search_recon",
            module_path="sage/c2/frontier_scanner.py",
            relationship=JigsawRelationship.SERVICE,
            description="External intelligence & repository recon probe",
        ),
        SubsystemRegistration(
            subsystem_id="gemini_recon_probe",
            module_path="sage/c2/gemini_recon_probe.py",
            relationship=JigsawRelationship.SERVICE,
            description="Gemini environment capability reconnaissance probe",
        ),
        SubsystemRegistration(
            subsystem_id="capability_graph",
            module_path="sage/c2/capability_graph.py",
            relationship=JigsawRelationship.SERVICE,
            description="AST-driven capability graph discovery and expansion",
        ),
        SubsystemRegistration(
            subsystem_id="execution_cell_attestation",
            module_path="sage/c2/execution_cell_contract.py",
            relationship=JigsawRelationship.SERVICE,
            description="Execution cell contract and cryptographic attestation fabric",
        ),
        SubsystemRegistration(
            subsystem_id="chatgpt_immersion",
            module_path="sage/c2/chatgpt_immersion.py",
            relationship=JigsawRelationship.PROJECTION,
            description="ChatGPT C2 immersion response adapter and organism tag",
        ),
        SubsystemRegistration(
            subsystem_id="chatgpt_runtime",
            module_path="sage/c2/chatgpt_runtime.py",
            relationship=JigsawRelationship.PROJECTION,
            description="ChatGPT C2 runtime entry point and response builder",
        ),
        SubsystemRegistration(
            subsystem_id="observatory_hud",
            module_path="sage/experimental/observatory/",
            relationship=JigsawRelationship.PROJECTION,
            description="Customer Observatory HUD & state projection",
        ),
        SubsystemRegistration(
            subsystem_id="customer_workbench",
            module_path="sage/business/customer_workbench.py",
            relationship=JigsawRelationship.PROJECTION,
            description="Customer value & workflow economics measurement projection",
        ),
        SubsystemRegistration(
            subsystem_id="capability_warehouse",
            module_path="sage/c2/capability_warehouse.py",
            relationship=JigsawRelationship.EVIDENCE_LEARNING,
            description="Long-term capability store & promotion engine",
        ),
        SubsystemRegistration(
            subsystem_id="experiment_ledger",
            module_path="sage/c2/experiment_ledger.py",
            relationship=JigsawRelationship.EVIDENCE_LEARNING,
            description="Orthogonal experiment ledger and verification evidence store",
        ),
        SubsystemRegistration(
            subsystem_id="live_operation_receipt",
            module_path="sage/c2/live_operation_receipt.py",
            relationship=JigsawRelationship.EVIDENCE_LEARNING,
            description="Cryptographic live operation receipts and verification",
        ),
        SubsystemRegistration(
            subsystem_id="airspace_manager",
            module_path="sage/experimental/airspace/manager.py",
            relationship=JigsawRelationship.EVIDENCE_LEARNING,
            description="Airspace manager event ledger and state reconstruction",
        ),
        SubsystemRegistration(
            subsystem_id="fleet_qualification_ledger",
            module_path="sage/experimental/airspace/fleet_qualification_ledger.py",
            relationship=JigsawRelationship.EVIDENCE_LEARNING,
            description="Fleet XP, proof, and military rank qualification ledger",
        ),
        SubsystemRegistration(
            subsystem_id="ccl_feedback_bridge",
            module_path="sage/experimental/cognitive/ccl_feedback_bridge.py",
            relationship=JigsawRelationship.EVIDENCE_LEARNING,
            description="Cognitive learning & feedback loop bridge",
        ),
    ]


def detect_duplicate_authorities(catalog: list[SubsystemRegistration]) -> list[str]:
    """Scan catalog for illegal duplicate domain claims and missing module disk paths."""
    conflicts: list[str] = []
    domain_map: dict[str, list[str]] = {}

    for sub in catalog:
        # Verify module path existence on disk
        p = Path(sub.module_path)
        if not p.exists():
            conflicts.append(
                f"Missing module path on disk for subsystem '{sub.subsystem_id}': '{sub.module_path}'"
            )

        if sub.authoritative_domain:
            domain_map.setdefault(sub.authoritative_domain, []).append(sub.subsystem_id)

    for domain, sys_ids in domain_map.items():
        if len(sys_ids) > 1:
            conflicts.append(f"Duplicate authority detected for domain '{domain}': {sys_ids}")
    return conflicts


def _verify_gate_live(
    gate_id: str,
    gate_name: str,
    source: str,
    target: str,
    commit_sha: str,
    module_check: str,
    symbol_check: str,
    contract_name: str,
) -> ConnectiveTissueGate:
    """Perform live disk and symbol inspection for a connective tissue gate."""
    passed = False
    details: dict[str, Any] = {"status": "UNVERIFIED", "contract": contract_name}

    try:
        if Path(module_check).exists():
            # If it's a python module file, attempt symbol load
            if module_check.endswith(".py"):
                mod_name = module_check.replace("/", ".").removesuffix(".py")
                mod = importlib.import_module(mod_name)
                if hasattr(mod, symbol_check):
                    passed = True
                    details["status"] = "VERIFIED"
                    details["symbol_found"] = symbol_check
                else:
                    details["error"] = f"Symbol '{symbol_check}' missing in module '{mod_name}'"
            else:
                passed = True
                details["status"] = "VERIFIED"
                details["path_found"] = module_check
        else:
            details["error"] = f"Module path '{module_check}' not found on disk"
    except Exception as exc:
        details["error"] = f"Live verification error: {exc}"

    return ConnectiveTissueGate(
        gate_id=gate_id,
        gate_name=gate_name,
        source_organ=source,
        target_organ=target,
        passed=passed,
        evidence_ref=f"SHA256:{commit_sha[:8]}:{gate_id}",
        details=details,
    )


def verify_10_connective_tissue_gates(commit_sha: str) -> list[ConnectiveTissueGate]:
    """Execute live evaluation for all 10 Connective Tissue Integration Gates."""
    gate_specs = [
        (
            "GATE-1",
            "Mission Intake -> C2 Core",
            "Mission Intake",
            "C2 Core",
            "sage/c2/frontier_admission.py",
            "FrontierAdmissionEngine",
            "SAGE_EXECUTABLE_MISSION_CONTRACT_SPEC_V1",
        ),
        (
            "GATE-2",
            "C2 Core -> Super Search / Recon",
            "C2 Core",
            "Super Search / Recon",
            "sage/c2/frontier_scanner.py",
            "scan_python_frontier",
            "SAGE_DEEP_RECON_VELOCITY_POLICY",
        ),
        (
            "GATE-3",
            "Recon -> Frontier Planner",
            "Super Search / Recon",
            "Frontier Planner",
            "sage/c2/frontier_intelligence_bridge.py",
            "FrontierIntelligenceBridge",
            "SAGE_FRONTIER_PLANNING_CONTRACT",
        ),
        (
            "GATE-4",
            "Frontier Planner -> Five Flights",
            "Frontier Planner",
            "Five Flights",
            "sage/c2/multi_frontier_dispatch.py",
            "MultiFrontierDispatcher",
            "SAGE_FIVE_FLIGHT_DISPATCH_CONTRACT",
        ),
        (
            "GATE-5",
            "Five Flights -> Evidence Capture",
            "Five Flights",
            "Evidence Capture",
            "sage/c2/live_operation_receipt.py",
            "LiveOperationReceipt",
            "SAGE_EVIDENCE_RECEIPT_SPEC",
        ),
        (
            "GATE-6",
            "Evidence Capture -> Independent Verification",
            "Evidence Capture",
            "Independent Verification",
            "sage/c2/chatgpt_c2_contract.py",
            "C2DirectiveDecision",
            "SAGE_INDEPENDENT_VERIFICATION_CONTRACT",
        ),
        (
            "GATE-7",
            "Verification -> Customer Surface (Observatory HUD)",
            "Independent Verification",
            "Observatory HUD",
            "sage/experimental/observatory/server.py",
            "app",
            "SAGE_OBSERVATORY_SURFACE_CONTRACT",
        ),
        (
            "GATE-8",
            "Customer Surface -> Economic Measurement",
            "Observatory HUD",
            "Economic Measurement",
            "sage/business/customer_workbench.py",
            "CustomerWorkbench",
            "SAGE_WORKBENCH_MEASUREMENT_CONTRACT",
        ),
        (
            "GATE-9",
            "Economic Measurement -> Capability Warehouse",
            "Economic Measurement",
            "Capability Warehouse",
            "sage/c2/capability_warehouse.py",
            "CapabilityWarehouseEngine",
            "SAGE_CAPABILITY_WAREHOUSE_CONTRACT",
        ),
        (
            "GATE-10",
            "Capability Warehouse -> Next Mission",
            "Capability Warehouse",
            "Next Mission Intake",
            "sage/experimental/sagi/metacognition.py",
            "MetacognitiveEngine",
            "SAGE_COGNITIVE_REHYDRATION_CONTRACT",
        ),
    ]

    return [
        _verify_gate_live(
            gate_id=gid,
            gate_name=gname,
            source=src,
            target=tgt,
            commit_sha=commit_sha,
            module_check=mpath,
            symbol_check=sym,
            contract_name=cname,
        )
        for gid, gname, src, tgt, mpath, sym, cname in gate_specs
    ]


def _get_active_commit_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    except Exception:
        return "0" * 40


def _compute_receipt_hash(
    receipt_id: str,
    commit_sha: str,
    subsystem_count: int,
    duplicate_authorities_detected: int,
    gates_evaluated: int,
    gates_passed: int,
    all_gates_passed: bool,
    subsystems: list[dict[str, Any]],
    gate_results: list[dict[str, Any]],
) -> str:
    payload = {
        "receipt_id": receipt_id,
        "commit_sha": commit_sha,
        "subsystem_count": subsystem_count,
        "duplicate_authorities_detected": duplicate_authorities_detected,
        "gates_evaluated": gates_evaluated,
        "gates_passed": gates_passed,
        "all_gates_passed": all_gates_passed,
        "subsystems": subsystems,
        "gate_results": gate_results,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class OrganismJigsawEngine:
    """Engine executing dynamic subsystem taxonomy audits and live gate integration verification."""

    def __init__(self, commit_sha: str | None = None):
        self.commit_sha = commit_sha or _get_active_commit_sha()
        self.subsystems = get_canonical_subsystem_catalog()

    def execute(self) -> OrganismVerificationReceipt:
        conflicts = detect_duplicate_authorities(self.subsystems)
        gate_results = verify_10_connective_tissue_gates(self.commit_sha)

        gates_evaluated = len(gate_results)
        gates_passed = sum(1 for g in gate_results if g.passed)
        all_gates_passed = (gates_passed == gates_evaluated) and (len(conflicts) == 0)

        receipt_id = f"organism_jigsaw_{self.commit_sha[:8]}"
        receipt_hash = _compute_receipt_hash(
            receipt_id=receipt_id,
            commit_sha=self.commit_sha,
            subsystem_count=len(self.subsystems),
            duplicate_authorities_detected=len(conflicts),
            gates_evaluated=gates_evaluated,
            gates_passed=gates_passed,
            all_gates_passed=all_gates_passed,
            subsystems=[s.model_dump() for s in self.subsystems],
            gate_results=[g.model_dump() for g in gate_results],
        )

        return OrganismVerificationReceipt(
            receipt_id=receipt_id,
            commit_sha=self.commit_sha,
            subsystem_count=len(self.subsystems),
            duplicate_authorities_detected=len(conflicts),
            gates_evaluated=gates_evaluated,
            gates_passed=gates_passed,
            all_gates_passed=all_gates_passed,
            receipt_hash=receipt_hash,
            subsystems=self.subsystems,
            gate_results=gate_results,
        )
