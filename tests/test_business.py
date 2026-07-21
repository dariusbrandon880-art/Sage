"""Tests for SAGE Business/Application Layer."""

import pytest
from sage.business.core import ClientWorkspaceSandbox, ContinuousPipeline, ComplianceRegistry


def test_client_workspace_sandbox():
    """Test client data and configuration isolation in sandboxed spaces."""
    sandbox_a = ClientWorkspaceSandbox(client_id="client_alpha")
    sandbox_b = ClientWorkspaceSandbox(client_id="client_beta")

    # 1. Config isolation
    sandbox_a.set_config("log_level", "DEBUG")
    sandbox_b.set_config("log_level", "INFO")
    assert sandbox_a.configs["log_level"] == "DEBUG"
    assert sandbox_b.configs["log_level"] == "INFO"

    # 2. Record sandboxing
    sandbox_a.add_record("record_01", {"name": "Alpha Project"})
    sandbox_b.add_record("record_01", {"name": "Beta Project"})

    records_a = sandbox_a.get_records()
    records_b = sandbox_b.get_records()
    assert len(records_a) == 1
    assert len(records_b) == 1
    assert records_a[0]["client_id"] == "client_alpha"
    assert records_b[0]["client_id"] == "client_beta"


def test_continuous_pipeline_execution():
    """Test stages execution and state tracking in continuous pipelines."""
    pipeline = ContinuousPipeline("deploy_pipeline", ["compile", "test", "deploy"])
    status = pipeline.get_pipeline_status()
    assert status == {"compile": "pending", "test": "pending", "deploy": "pending"}

    # Execute first stage successfully
    success = pipeline.execute_stage("compile", lambda: True)
    assert success is True
    assert pipeline.get_pipeline_status()["compile"] == "completed"

    # Execute second stage with failure callback
    success_fail = pipeline.execute_stage("test", lambda: False)
    assert success_fail is False
    assert pipeline.get_pipeline_status()["test"] == "failed"

    # Execute missing stage raise error
    with pytest.raises(ValueError):
        pipeline.execute_stage("optimize", lambda: True)


def test_compliance_registry_evaluations():
    """Test evaluating compliance registry rules against data structures."""
    registry = ComplianceRegistry()

    # Rule: checks that any decision has an evidence list of size > 0
    registry.add_rule(
        name="Require Evidence Rule",
        validator_callable=lambda d: len(d.get("evidence", [])) > 0,
        severity="high"
    )

    # Compliant structure
    compliant_decision = {"description": "A", "evidence": ["fact_1"]}
    eval1 = registry.evaluate_compliance(compliant_decision)
    assert eval1["compliant"] is True
    assert eval1["score"] == 1.0

    # Non-compliant structure
    non_compliant_decision = {"description": "B", "evidence": []}
    eval2 = registry.evaluate_compliance(non_compliant_decision)
    assert eval2["compliant"] is False
    assert len(eval2["failed_rules"]) == 1
    assert eval2["failed_rules"][0]["rule"] == "Require Evidence Rule"
    assert eval2["score"] == 0.0
