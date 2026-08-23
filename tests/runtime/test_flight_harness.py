import json
import pytest
from sage.runtime.flight_harness import SAGEGPTFlightHarness
from sage.runtime.engine import SageRuntime


def test_flight_harness_executes_comparative_benchmark():
    runtime = SageRuntime()
    runtime.set_objective("Benchmark Flight Objective")

    harness = SAGEGPTFlightHarness(runtime)
    prompt = "Validate C2 context binding"

    comparison = harness.run_comparative_flight(prompt)

    assert comparison.flight_a.is_roleplay is True
    assert not comparison.flight_b.is_roleplay
    assert comparison.overall_binding_score > 0.0
    assert "deltas" in comparison.metrics


def test_flight_harness_generates_evidence_receipt(tmp_path):
    output_file = str(tmp_path / "binding_evidence.json")
    runtime = SageRuntime()
    harness = SAGEGPTFlightHarness(runtime)

    harness.run_comparative_flight("Run receipt verification", output_path=output_file)

    with open(output_file, "r") as f:
        data = json.load(f)

    assert data["status"] == "VALIDATED_COMPARATIVE_PROOF"
    assert "attestation" in data
    assert data["attestation"]["signer_identity"] == "SAGE_C2_GOVERNOR"
