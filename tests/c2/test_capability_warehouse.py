"""Unit and integration tests for SAGE Capability Warehouse Auto-Promotion Engine."""

import pytest
import shutil
from pathlib import Path

from sage.c2.capability_warehouse import (
    CapabilityWarehouseEngine,
    PromotionStatus,
    WarehouseItem,
    WarehousePromotionReceipt,
)


@pytest.fixture
def temp_warehouse_path(tmp_path):
    return str(tmp_path / "temp_warehouse_registry.json")


@pytest.fixture
def temp_op_registry_path(tmp_path):
    dest = tmp_path / "temp_op_registry.json"
    shutil.copy("evidence_capture/operational_capability_registry.json", dest)
    return str(dest)


@pytest.fixture
def warehouse_engine(temp_warehouse_path, temp_op_registry_path):
    return CapabilityWarehouseEngine(
        storage_path=temp_warehouse_path,
        op_registry_path=temp_op_registry_path,
    )


@pytest.fixture
def valid_sha():
    return "56b41ede32bbf21f2a0dc59ec852667f8f4989e6"


def test_warehouse_initialization(warehouse_engine):
    items = warehouse_engine.list_items()
    assert isinstance(items, list)


def test_promote_wave_capabilities_success(warehouse_engine, valid_sha):
    items_to_promote = [
        {
            "capability_id": "CAP-MULTI-SESSION-VELOCITY",
            "name": "Multi-Session Velocity Engine",
            "description": "Governs multi-session parallel Big Jump Waves under Rolls-Royce Quality Standard",
            "reusable_patterns": ["Pattern: Anti-Collision Locking", "Pattern: 20-Cell Advancement"],
            "evidence_references": ["evidence_capture/multi_session_velocity_wave_evidence.json"],
            "test_references": ["tests/c2/test_workflow_velocity.py"],
        }
    ]

    receipt = warehouse_engine.promote_wave_capabilities(
        wave_id="multi_session_velocity_wave_001",
        exact_git_head=valid_sha,
        items_to_promote=items_to_promote,
        reconvergence_verdict="PASS",
        rolls_royce_passed=True,
    )

    assert receipt.wave_id == "multi_session_velocity_wave_001"
    assert receipt.exact_git_head == valid_sha
    assert receipt.promoted_items_count == 1
    assert "CAP-MULTI-SESSION-VELOCITY" in receipt.promoted_capability_ids
    assert receipt.rolls_royce_passed is True
    assert len(receipt.receipt_hash) == 64

    # Verify item lookup
    item = warehouse_engine.get_item("wh_cap_multi_session_velocity")
    assert item is not None
    assert item.capability_id == "CAP-MULTI-SESSION-VELOCITY"
    assert item.promotion_status == PromotionStatus.PROMOTED
    assert len(item.reusable_patterns) == 2


def test_invalid_sha_rejection(warehouse_engine):
    items = [
        {
            "capability_id": "CAP-TEST",
            "name": "Test Capability",
            "evidence_references": ["ev.json"],
            "test_references": ["test.py"],
        }
    ]
    with pytest.raises(ValueError, match="Invalid exact git HEAD commit SHA"):
        warehouse_engine.promote_wave_capabilities(
            wave_id="invalid_wave",
            exact_git_head="short_sha",
            items_to_promote=items,
        )


def test_unverified_wave_promotion_rejection(warehouse_engine, valid_sha):
    items = [
        {
            "capability_id": "CAP-TEST",
            "name": "Test Capability",
            "evidence_references": ["ev.json"],
            "test_references": ["test.py"],
        }
    ]
    with pytest.raises(ValueError, match="Cannot promote capabilities from an unverified or failed wave."):
        warehouse_engine.promote_wave_capabilities(
            wave_id="failed_wave",
            exact_git_head=valid_sha,
            items_to_promote=items,
            reconvergence_verdict="FAIL_CLOSED",
            rolls_royce_passed=False,
        )


def test_missing_evidence_or_test_proof_fails_closed(warehouse_engine, valid_sha):
    items_missing_evidence = [
        {
            "capability_id": "CAP-NO-EVID",
            "name": "No Evidence Capability",
            "evidence_references": [],
            "test_references": ["test.py"],
        }
    ]
    with pytest.raises(ValueError, match="missing evidence or test references"):
        warehouse_engine.promote_wave_capabilities(
            wave_id="no_evid_wave",
            exact_git_head=valid_sha,
            items_to_promote=items_missing_evidence,
        )

    items_missing_tests = [
        {
            "capability_id": "CAP-NO-TEST",
            "name": "No Test Capability",
            "evidence_references": ["ev.json"],
            "test_references": [],
        }
    ]
    with pytest.raises(ValueError, match="missing evidence or test references"):
        warehouse_engine.promote_wave_capabilities(
            wave_id="no_test_wave",
            exact_git_head=valid_sha,
            items_to_promote=items_missing_tests,
        )
