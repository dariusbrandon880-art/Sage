"""Unit tests for Capability Warehouse Promotion Engine."""

import pytest
from sage.capability_registry import SAGEOperationalCapabilityRegistry
from sage.c2.capability_warehouse import CapabilityWarehouseEngine, PromotionStatus
from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
)

VALID_SHA = "bcb01b4c73087a38b556942f7c030d5ef855fa3e"


def test_capability_warehouse_promotion_success(tmp_path):
    registry_file = tmp_path / "test_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))
    engine = CapabilityWarehouseEngine(registry=registry)

    synthesizer = C2ReconvergenceSynthesizer(wave_id="wave-wh-001")
    flights = []
    for i in range(1, 6):
        milestones = [
            LifecycleMilestoneRecord(stage=s, passed=True, evidence_ref=f"ref_{i}")
            for s in LifecycleStage
        ]
        flights.append(
            FlightExecutionSummary(
                flight_id=f"F{i}",
                target=f"target_{i}",
                classification="ACTIVE",
                execution_result="PASS",
                exact_head=VALID_SHA,
                tests_passed=10,
                evidence_ref=f"evidence_{i}.json",
                pr_or_change=f"PR #{i}",
                lifecycle_milestones=milestones,
            )
        )

    pkg = synthesizer.synthesize_reconvergence(flights)
    rcpt = engine.promote_wave_package(pkg, exact_git_head=VALID_SHA)

    assert rcpt.status == PromotionStatus.PROMOTED
    assert rcpt.promoted_capabilities_count == 5
    assert len(rcpt.receipt_hash) == 64
    assert registry.get_capability("CAP-WH-WAVE-WH-001-F1") is not None
