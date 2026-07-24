"""SAGE ACR-X C3S adversarial validation and falsification tests.

Implements Test 1 (Clean Continuity Path), Test 2 (Continuity Attack / Memory Poisoning),
and Test 3 (Recovery Fidelity) to evaluate the cognitive substrate validation gates.
"""

import json
import tempfile
from pathlib import Path

import pytest

from sage.core.acrx_kernel import ACRXKernel
from sage.core.acrx_models import STPMemoryLayer
from sage.core.proofreader import ACRXProofreader
from sage.runtime import SAGERuntime


@pytest.fixture
def temp_runtime_and_audit():
    """Fixture to provide SAGERuntime and clean audit path in temporary folders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runtime = SAGERuntime(workspace_path=tmpdir)
        runtime.start()

        # Setup stable task/objective BEFORE booting kernel so baseline state is populated
        runtime.set_objective("Launch Orion Rocket")
        runtime.set_task("Check oxygen valves")

        audit_path = Path(tmpdir) / "audit"
        kernel = ACRXKernel(runtime, vault_dir=str(audit_path))
        kernel.boot()
        yield runtime, kernel, audit_path
        runtime.stop()


def test_clean_continuity_path(temp_runtime_and_audit):
    """Test 1: Clean Continuity Path.

    Verifies identity coherence remains true, valid memory promotion occurs,
    and audit records are successfully created.
    """
    _, kernel, audit_path = temp_runtime_and_audit

    # Ingest a clean SAGE-SKAL ValidationReport
    clean_payload = {
        "source": "ci-oxygen-tests",
        "timestamp": "2026-07-24T12:00:00Z",
        "commit_identifier": "orion-v1.0",
        "validation_results": {"valve_check": "nominal", "pressure_psi": 120.5},
        "evidence_references": ["sensor-log-ox1"],
        "confidence_metadata": {"reliability_index": 1.0},
    }

    # Life-cycle step: INGEST
    token_id = kernel.ingest(clean_payload)
    assert token_id is not None

    # Life-cycle step: EVALUATE & VERIFY
    metrics = kernel.evaluate()
    assert metrics["shannon_entropy"] < 6.0
    assert metrics["idi"] == 0.0  # Same as current baseline

    is_valid = kernel.verify()
    assert is_valid is True
    assert kernel.is_coherent is True

    # Life-cycle step: CONSOLIDATE & ATTEST
    consolidated = kernel.consolidate()
    assert consolidated is True

    # Check token resides in SEMANTIC store now
    semantic_tokens = kernel.fabric.list_layer_tokens(STPMemoryLayer.SEMANTIC)
    assert len(semantic_tokens) == 1
    assert semantic_tokens[0].content["source"] == "ci-oxygen-tests"

    # Attest & Audit creation
    kernel.attest("Oxygen valve verification completed with nominal metrics.")

    vault_file = audit_path / "c3s_vault.json"
    log_file = audit_path / "identity_timeline.log"

    assert vault_file.exists()
    assert log_file.exists()

    with open(vault_file, "r") as f:
        vault_data = json.load(f)
    assert vault_data["is_coherent"] is True
    assert "Oxygen valve verification completed" in vault_data["last_attestation"]


def test_continuity_attack_memory_poisoning(temp_runtime_and_audit):
    """Test 2: Continuity Attack / Memory Poisoning.

    Injects chaotic payloads, abnormal structural entropy, and conflicting state data,
    verifying continuity gates block unsafe consolidation.
    """
    runtime, kernel, audit_path = temp_runtime_and_audit

    # Inject a massive drift: simulate a poisoning attack that mutates the active task
    # and appends numerous fake blockers/dependencies, bloating the observed state vector
    runtime.set_task("POISONED INJECTED STATE")
    for i in range(10):
        runtime.add_blocker(f"Fake Blocked Thread {i}")
        runtime.current_state.dependencies.append(f"Fake Dep {i}")

    # Create a chaotic payload designed to trigger massive Shannon structural entropy
    # (High randomness / randomized string data)
    chaotic_string = (
        "q1w2e3r4t5y6u7i8o9p0" * 50
    )  # Highly random distribution, extremely high length
    chaotic_payload = {
        "source": "malicious-injection-vector",
        "timestamp": "2026-07-24T12:00:00Z",
        "commit_identifier": "hack-abc",
        "validation_results": {"entropy_attack": chaotic_string},
        "evidence_references": [chaotic_string],
        "confidence_metadata": {"hijack": True},
    }

    # Life-cycle step: INGEST
    token_id = kernel.ingest(chaotic_payload)
    assert token_id is not None

    # Life-cycle step: EVALUATE & VERIFY
    metrics = kernel.evaluate()
    # Shannon structural entropy should exceed safe threshold
    assert metrics["shannon_entropy"] > 3.0
    # Identity Drift Index (IDI) must be abnormally high due to injected task and 10 blockers
    assert metrics["idi"] > 1.5

    is_valid = kernel.verify()
    assert is_valid is False  # Instability detected, gate failed!
    assert kernel.is_coherent is False

    # Life-cycle step: CONSOLIDATE (should fail and block promotion)
    consolidated = kernel.consolidate()
    assert consolidated is False

    # Check SEMANTIC store has zero tokens promoted from this injection
    semantic_tokens = kernel.fabric.list_layer_tokens(STPMemoryLayer.SEMANTIC)
    assert len(semantic_tokens) == 0

    # Attest unverified/incoherent state
    kernel.attest("Continuity gate triggered: extreme state drift and anomalous entropy detected.")

    vault_file = audit_path / "c3s_vault.json"
    with open(vault_file, "r") as f:
        vault_data = json.load(f)
    assert vault_data["is_coherent"] is False
    assert "Continuity gate triggered" in vault_data["last_attestation"]


def test_recovery_fidelity(temp_runtime_and_audit):
    """Test 3: Recovery Fidelity.

    Verifies state reports are reconstructed correctly, the audit chain survives
    interruption, and metrics remain fully consistent.
    """
    runtime, kernel, audit_path = temp_runtime_and_audit

    # 1. Capture original stable state before interruption
    runtime.set_objective("Secure Gateway")
    runtime.set_task("Sync tokens")
    runtime.add_blocker("Missing workspace keys")

    pre_state = {
        "current_objective": runtime.current_state.current_objective,
        "active_task": runtime.current_state.active_task,
        "blockers": list(runtime.current_state.blockers),
        "dependencies": list(runtime.current_state.dependencies),
    }

    # Re-initialize kernel to snaphost this pre_state
    kernel.boot()

    # Ingest clean token and attest
    kernel.ingest({"source": "rec-test"})
    kernel.consolidate()
    kernel.attest("State snapshot verified before mock crash.")

    # 2. Mock crash / interruption (Clear active runtime variables)
    runtime.current_state.current_objective = None
    runtime.current_state.active_task = None
    runtime.current_state.blockers.clear()
    runtime.current_state.dependencies.clear()

    # 3. Simulate restoration & rehydration from latest snapshot
    # Here we recover using the kernel baseline state from the audit vault
    restored_kernel = ACRXKernel(runtime, vault_dir=str(audit_path))
    restored_kernel.boot()

    post_state = restored_kernel.baseline_state

    # 4. Measure Recovery Fidelity (RF)
    rf = ACRXProofreader.calculate_recovery_fidelity(pre_state, post_state)
    assert rf == 1.0  # Perfect restoration!

    # Verify audit timeline survives the crash
    log_file = audit_path / "identity_timeline.log"
    assert log_file.exists()
    with open(log_file, "r") as f:
        log_content = f.read()
    assert "snapshot verified before mock crash" in log_content
