from sage.capability_registry import SAGEOperationalCapabilityRegistry
from sage.c2.capability_warehouse import CapabilityWarehouseEngine, PromotionStatus
from sage.c2.reconvergence_synthesizer import C2ReconvergenceSynthesizer, FlightExecutionSummary, LifecycleMilestoneRecord, LifecycleStage

VALID_SHA = "7cdebce6e542ab5e8975194c6610f388e83942a9"

def test_warehouse_promotes_complete_wave(tmp_path):
    registry=SAGEOperationalCapabilityRegistry(storage_path=str(tmp_path/"registry.json"))
    engine=CapabilityWarehouseEngine(registry=registry); synth=C2ReconvergenceSynthesizer(wave_id="wave-wh-001")
    flights=[]
    for i in range(1,6):
        milestones=[LifecycleMilestoneRecord(stage=s, passed=True, evidence_ref=f"ref_{i}") for s in LifecycleStage]
        flights.append(FlightExecutionSummary(flight_id=f"F{i}",target=f"target_{i}",classification="ACTIVE",execution_result="PASS",exact_head=VALID_SHA,tests_passed=10,evidence_ref=f"evidence_{i}.json",pr_or_change=f"PR #{i}",lifecycle_milestones=milestones))
    rcpt=engine.promote_wave_package(synth.synthesize_reconvergence(flights), exact_git_head=VALID_SHA)
    assert rcpt.status == PromotionStatus.PROMOTED and rcpt.promoted_capabilities_count == 5
