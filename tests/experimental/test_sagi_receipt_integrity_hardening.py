"""Adversarial hardening tests for SAGI evolution receipt integrity."""

from sage.experimental.sagi.controller import SAGIEvolutionController, SAGIEvolutionReceipt


def test_evolution_receipt_self_integrity_passes():
    controller = SAGIEvolutionController()
    receipt = controller.execute_evolution_cycle()

    assert receipt.verify_integrity() is True
    assert receipt.receipt_sha256 == receipt.compute_sha256()


def test_evolution_receipt_reasoning_tamper_is_detected():
    controller = SAGIEvolutionController()
    receipt = controller.execute_evolution_cycle()
    original_hash = receipt.receipt_sha256

    receipt.decision_reasoning = "TAMPERED_REASONING"

    assert receipt.receipt_sha256 == original_hash
    assert receipt.verify_integrity() is False


def test_evolution_receipt_learning_metrics_tamper_is_detected():
    controller = SAGIEvolutionController()
    receipt = controller.execute_evolution_cycle()
    original_hash = receipt.receipt_sha256

    receipt.learning_metrics["success_rate"] = 999.0

    assert receipt.receipt_sha256 == original_hash
    assert receipt.verify_integrity() is False


def test_evolution_receipt_hash_covers_operational_fields():
    controller = SAGIEvolutionController()
    receipt = controller.execute_evolution_cycle()

    for field, value in (
        ("proposal_id", "tampered-proposal"),
        ("verification_status", "TAMPERED"),
        ("temperature_after", 99.0),
        ("failure_memory_count", 999),
        ("timestamp", 0.0),
    ):
        candidate = SAGIEvolutionReceipt.model_validate(receipt.model_dump())
        setattr(candidate, field, value)
        assert candidate.verify_integrity() is False
