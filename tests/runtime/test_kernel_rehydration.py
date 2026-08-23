import json
from types import SimpleNamespace

from sage.runtime.model_gateway import (
    C2RehydrationEngine,
    KernelDecisionBridge,
    SAGEActionProposal,
    SAGEOperatingContext,
)
from sage.runtime.engine import SageRuntime


def test_rehydration_engine_constructs_digestable_context():
    runtime = SageRuntime()
    runtime.set_objective("Test Kernel Objective")
    runtime.set_task("Test Kernel Task")

    c2_ctx_dict = runtime.get_c2_context()

    assert c2_ctx_dict["active_objective"] == "Test Kernel Objective"
    assert c2_ctx_dict["active_task"] == "Test Kernel Task"
    assert "context_digest" in c2_ctx_dict
    assert len(c2_ctx_dict["context_digest"]) == 64


def test_kernel_decision_bridge_binds_proposals():
    proposal = SAGEActionProposal(
        action_type="RECON",
        target="sage/runtime/engine.py",
        parameters={"depth": 2},
        justification="Verify kernel rehydration hook",
    )

    decision_dict = KernelDecisionBridge.bind_proposal_to_decision(
        proposal, session_id="test_sess_123", evidence_refs=("ref_kernel_001",)
    )

    assert decision_dict["id"].startswith("dec_kernel_")
    assert decision_dict["decision_type"] == "technical"
    assert "RECON" in decision_dict["description"]
    assert decision_dict["evidence"] == ["ref_kernel_001"]
    assert decision_dict["outcome"] == "BOUND_UNDER_SAGE_GOVERNANCE"
