from sage.business.customer_workbench import CustomerWorkflowMeasurement, CustomerWorkbench
from sage.c2.operator_acceptance_bootstrap import OperatorAcceptanceBootstrap
from sage.c2.mission_continuity import CANONICAL_MAIN_GOALS


def build_state():
    bootstrap = OperatorAcceptanceBootstrap()
    state = bootstrap.rehydrate(
        mission_id="SAGE Operational Convergence",
        main_goals=list(CANONICAL_MAIN_GOALS),
        side_goals=[],
        active_flights=["F1", "F2", "F3", "F4", "F5"],
        required_interfaces=["chatgpt", "gemini", "jules", "observatory_hud"],
    )
    return bootstrap.bind_customer_surface(
        state,
        "SAGE_FIRST_CUSTOMER",
        "FIRST_CUSTOMER_WORKBENCH",
        "[SAGE::C2::CHATGPT]",
    )


def test_first_customer_workbench_preserves_governed_acceptance_boundary():
    state = build_state()
    snapshot = CustomerWorkbench().snapshot(state, ["F1", "F2", "F3", "F4", "F5"])
    assert snapshot.customer_id == "SAGE_FIRST_CUSTOMER"
    assert snapshot.agent_identity == "[SAGE::C2::CHATGPT]"
    assert snapshot.deterministic_status == "PASS"
    assert snapshot.empirical_status == "PENDING"
    assert snapshot.acceptance_status == "ENGINEERING_VERIFIED"
    assert snapshot.mission_goals[0] == "mission continuity"


def test_workflow_measurement_computes_completed_workflow_value():
    measurement = CustomerWorkflowMeasurement(
        workflow_id="first_customer_mission_001",
        completed=True,
        human_interventions=2,
        execution_seconds=120.0,
        direct_cost_usd=4.50,
        value_usd=25.0,
        reusable_capability="governed mission receipt",
        failure_count=1,
        recovery_count=1,
        evidence_refs=["evidence/receipt.json"],
    )
    assert measurement.net_value_usd == 20.5
    workbench = CustomerWorkbench()
    workbench.record_workflow(measurement)
    assert workbench.measurements[0].workflow_id == "first_customer_mission_001"


def test_invalid_workflow_measurement_is_rejected():
    try:
        CustomerWorkbench().record_workflow(CustomerWorkflowMeasurement(workflow_id="", human_interventions=-1))
    except ValueError as exc:
        assert "workflow_id" in str(exc)
    else:
        raise AssertionError("invalid workflow measurement was accepted")
