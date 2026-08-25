#!/usr/bin/env python3
"""SAGE Multi-Node Big Jump Wave Execution Script.

Executes an optional multi-node Big Jump Wave configuration (Nodes A, B, C) with 5 independent flights
+ up to 2 reserve slots per node, generating signed evidence in evidence_capture/multi_node_wave_evidence.json.
"""

import json
import logging
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from sage.c2.multi_node_wave import C2MultiNodeWaveEngine, NodeRole

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("execute_multi_node_wave")


def main():
    logger.info("Initializing Multi-Node Big Jump Wave Execution Engine...")
    engine = C2MultiNodeWaveEngine(repo_root=repo_root)

    wave_nodes = {
        "NODE_A": {
            "role": NodeRole.PRIMARY_REPAIR.value,
            "flights": [
                {
                    "flight_id": "NODE_A_F1",
                    "frontier_name": "Fleet & Station Governance",
                    "target_namespaces": ["sage/experimental/airspace/"],
                    "description": "Station identity, nametag badge, fleet rank state.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_A_F2",
                    "frontier_name": "C2 Contract & Command Fidelity",
                    "target_namespaces": ["sage/c2/chatgpt_c2_contract.py"],
                    "description": "ChatGPT exact-order anti-drift contract enforcement.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_A_F3",
                    "frontier_name": "Provenance & Attestation Substrate",
                    "target_namespaces": ["sage/c2/release_provenance.py"],
                    "description": "Cryptographic release provenance and attestation.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_A_F4",
                    "frontier_name": "Multi-Node Wave Execution Core",
                    "target_namespaces": ["sage/c2/multi_node_wave.py"],
                    "description": "Multi-node 5-flight execution engine.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_A_F5",
                    "frontier_name": "Evidence & Progression Lifecycle",
                    "target_namespaces": ["sage/c2/progression_receipt_serializer.py"],
                    "description": "Evidence receipt serialization and parent hashing.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_A_R1",
                    "frontier_name": "Node A Reserve Slot 1",
                    "target_namespaces": ["sage/c2/reserve_a1/"],
                    "description": "Reserve repair slot for discovered defect 1.",
                    "is_reserve": True,
                },
                {
                    "flight_id": "NODE_A_R2",
                    "frontier_name": "Node A Reserve Slot 2",
                    "target_namespaces": ["sage/c2/reserve_a2/"],
                    "description": "Reserve repair slot for discovered defect 2.",
                    "is_reserve": True,
                },
            ],
        },
        "NODE_B": {
            "role": NodeRole.INDEPENDENT_VERIFICATION.value,
            "flights": [
                {
                    "flight_id": "NODE_B_F1",
                    "frontier_name": "Multi-Node Unit Verification",
                    "target_namespaces": ["tests/c2/test_multi_node_wave.py"],
                    "description": "Multi-node wave unit and integration suite.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_B_F2",
                    "frontier_name": "Protocol Governance Suite",
                    "target_namespaces": ["tests/runtime/test_protocol_governance.py"],
                    "description": "System instruction and protocol governance tests.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_B_F3",
                    "frontier_name": "CCL Feedback Bridge Suite",
                    "target_namespaces": ["tests/experimental/test_ccl_feedback_bridge.py"],
                    "description": "Closed-loop capability outcome feedback verification.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_B_F4",
                    "frontier_name": "Fleet Readiness Suite",
                    "target_namespaces": ["tests/experimental/test_fleet_readiness.py"],
                    "description": "Airspace fleet readiness score verification.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_B_F5",
                    "frontier_name": "Security Audit Runner",
                    "target_namespaces": ["scripts/verify_security_posture.py"],
                    "description": "Security audit and secret scanner verification.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_B_R1",
                    "frontier_name": "Node B Reserve Slot 1",
                    "target_namespaces": ["tests/reserve_b1/"],
                    "description": "Reserve verification slot 1.",
                    "is_reserve": True,
                },
                {
                    "flight_id": "NODE_B_R2",
                    "frontier_name": "Node B Reserve Slot 2",
                    "target_namespaces": ["tests/reserve_b2/"],
                    "description": "Reserve verification slot 2.",
                    "is_reserve": True,
                },
            ],
        },
        "NODE_C": {
            "role": NodeRole.ADVERSARIAL_RESEARCH.value,
            "flights": [
                {
                    "flight_id": "NODE_C_F1",
                    "frontier_name": "Adversarial Forgery Analysis",
                    "target_namespaces": ["tests/c2/test_live_operation_receipt_provenance.py"],
                    "description": "Spoofed/replayed/mismatched live receipt attack analysis.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_C_F2",
                    "frontier_name": "Anti-Drift Contract Falsification",
                    "target_namespaces": ["tests/c2/test_chatgpt_c2_contract.py"],
                    "description": "Exact directive preservation & drift falsification.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_C_F3",
                    "frontier_name": "Supply Chain Tamper Suite",
                    "target_namespaces": ["sage/c2/supply_chain_attestation.py"],
                    "description": "SBOM and in-toto envelope tamper detection.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_C_F4",
                    "frontier_name": "Temporal Leakage Falsification",
                    "target_namespaces": ["sage/experimental/sports_longitudinal.py"],
                    "description": "Out-of-sample data separation & temporal leakage test.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_C_F5",
                    "frontier_name": "Governance Directives Conformance",
                    "target_namespaces": ["tests/test_governance_directives.py"],
                    "description": "Governance law and contract assertion test suite.",
                    "is_reserve": False,
                },
                {
                    "flight_id": "NODE_C_R1",
                    "frontier_name": "Node C Reserve Slot 1",
                    "target_namespaces": ["tests/reserve_c1/"],
                    "description": "Reserve adversarial slot 1.",
                    "is_reserve": True,
                },
                {
                    "flight_id": "NODE_C_R2",
                    "frontier_name": "Node C Reserve Slot 2",
                    "target_namespaces": ["tests/reserve_c2/"],
                    "description": "Reserve adversarial slot 2.",
                    "is_reserve": True,
                },
            ],
        },
    }

    receipt = engine.execute_multi_node_wave(
        wave_id="WAVE_MULTI_NODE_20260822_001",
        nodes=wave_nodes,
        attempted_flow_alteration=False,
    )

    evidence_path = repo_root / "evidence_capture" / "multi_node_wave_evidence.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(receipt.to_dict(), f, indent=2)

    logger.info("Multi-Node Big Jump Wave completed successfully.")
    logger.info(f"Reconvergence Verdict: {receipt.reconvergence_verdict}")
    logger.info(f"Receipt Hash: {receipt.receipt_hash}")
    logger.info(f"Evidence persisted at: {evidence_path}")


if __name__ == "__main__":
    main()
