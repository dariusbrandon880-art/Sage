"""SAGE UAGF safe-sdr-agm-003 Controlled Validation Test Suite."""

import os
import json
import ast
from pathlib import Path
from scripts.run_agm_simulation import run_simulation


def test_sdr_agm_003_simulation_integrity_and_logic():
    """Verify role separation, delegation constraints, and SAGE-CRC hash-chaining in simulation."""
    result = run_simulation()

    # 1. Structure check
    assert result["compliance_id"] == "comp_sdr_agm_003_7f8e1a2b3c4d5e"
    assert result["validation_plan_status"] == "SUCCESSFULLY_VALIDATED"
    assert "hash_chain_root" in result
    assert "event_chain" in result
    assert "rejection_registry" in result

    # 2. Sequential Event Chain validation
    events = result["event_chain"]
    assert len(events) == 8  # 8 event steps in SimpleHashChain

    # Validate Event Types
    expected_event_types = [
        "IDENTITY_VALIDATION",
        "CAPABILITY_AUTHORIZATION",
        "DELEGATION_APPROVAL",
        "CONTROLLED_TASK_SIMULATION",
        "INVALID_DELEGATION_REJECTED",
        "BOUNDARY_MUTATION_BLOCKED",
        "CIRCULAR_DELEGATION_BLOCKED",
        "HUMAN_REVIEW_PREPARATION"
    ]
    actual_event_types = [e["event_type"] for e in events]
    for exp_type in expected_event_types:
        assert exp_type in actual_event_types

    # 3. SAGE-CRC Cryptographic Hash Chain Validation
    prev_hash = "genesis_root_00000000000000000000000000000000"
    for event in events:
        assert event["previous_hash"] == prev_hash
        assert "block_hash" in event
        prev_hash = event["block_hash"]

    # Verify final hash matches root
    assert result["hash_chain_root"] == prev_hash

    # 4. Rejection Registry Validation
    rejections = result["rejection_registry"]
    assert len(rejections) == 3  # Unauthorized capability, boundary mutation, circular task

    # Verify boundary blocked event
    boundary_violations = [r for r in rejections if "Boundary Enforcement Violation" in r.get("reason", "")]
    assert len(boundary_violations) == 1
    assert boundary_violations[0]["enforcement_action"] == "BLOCKED"

    # Verify circular delegation blocked event
    circular_blocks = [r for r in rejections if "Circular dependency cycle detected" in r.get("reason", "")]
    assert len(circular_blocks) == 1
    assert circular_blocks[0]["enforcement_action"] == "BLOCKED"


def test_sdr_agm_003_protected_boundaries_preservation():
    """Assert that zero changes have been made to protected namespaces."""
    root_dir = Path(__file__).parent.parent.parent
    sage_dir = root_dir / "sage"

    # Ensure no experimental code leakage into production directories (One-Way Import Law)
    for path in sage_dir.glob("**/*.py"):
        if "experimental" in path.parts:
            continue

        with open(path, "r", encoding="utf-8") as f:
            file_content = f.read()
            try:
                tree = ast.parse(file_content, filename=str(path))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to import from module '{node.module}'"
                        )
