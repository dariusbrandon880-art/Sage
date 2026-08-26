"""Unit and adversarial tests for SAGE Governed Collaboration Memory Engine."""

import pytest
from sage.memory.collaboration_learning import (
    GovernedCollaborationMemoryEngine,
    KnowledgeScope,
    PromotionStage,
    PatternStatus,
)


def test_observe_pattern_initializes_in_observed_stage():
    engine = GovernedCollaborationMemoryEngine("407f7b52b161c520688bd8eef509146d86717c74")

    pattern = engine.observe_pattern(
        pattern_id="PAT-PREF-001",
        operator_id="operator-darius",
        observation="Operator prefers concise bullet summaries for C2 reports.",
        hypothesis="Concise formatting improves report clarity.",
        evidence_refs=["evidence_capture/chat_turn_001.json"],
        scope=KnowledgeScope.PERSONAL,
    )

    assert pattern.pattern_id == "PAT-PREF-001"
    assert pattern.stage == PromotionStage.OBSERVED
    assert pattern.status == PatternStatus.ACTIVE
    assert pattern.confidence_score == 0.5
    assert len(engine.receipts) == 1
    assert engine.receipts[0].receipt_hash == engine.receipts[0].compute_hash()


def test_evaluate_and_advance_pipeline():
    engine = GovernedCollaborationMemoryEngine("407f7b52b161c520688bd8eef509146d86717c74")

    pattern = engine.observe_pattern(
        pattern_id="PAT-PREF-002",
        operator_id="operator-darius",
        observation="Operator requests dynamic commit SHA derivation.",
        hypothesis="Dynamic SHA prevents hardcoded SHA drift.",
        evidence_refs=["evidence/obs1.json"],
    )

    # Stage 1 -> CANDIDATE
    p1 = engine.evaluate_and_advance("PAT-PREF-002", falsification_passed=True, evidence_ref="evidence/test1.json")
    assert p1.stage == PromotionStage.CANDIDATE
    assert p1.confidence_score == 0.7

    # Stage 2 -> TESTED
    p2 = engine.evaluate_and_advance("PAT-PREF-002", falsification_passed=True, evidence_ref="evidence/test2.json")
    assert p2.stage == PromotionStage.TESTED
    assert p2.confidence_score == 0.85

    # Stage 3 -> VALIDATED
    p3 = engine.evaluate_and_advance("PAT-PREF-002", falsification_passed=True, evidence_ref="evidence/val.json")
    assert p3.stage == PromotionStage.VALIDATED
    assert p3.confidence_score == 0.95


def test_contradicted_pattern_fails_closed():
    engine = GovernedCollaborationMemoryEngine("407f7b52b161c520688bd8eef509146d86717c74")

    pattern = engine.observe_pattern(
        pattern_id="PAT-JOKE-001",
        operator_id="operator-darius",
        observation="Operator jokingly said to delete the entire repo.",
        hypothesis="Operator wants repo deleted.",
    )

    # Falsification test fails
    p_contradicted = engine.evaluate_and_advance("PAT-JOKE-001", falsification_passed=False, evidence_ref="evidence/falsify.json")
    assert p_contradicted.status == PatternStatus.CONTRADICTED
    assert p_contradicted.stage == PromotionStage.OBSERVED
    assert p_contradicted.confidence_score == 0.0


def test_retire_pattern():
    engine = GovernedCollaborationMemoryEngine("407f7b52b161c520688bd8eef509146d86717c74")

    engine.observe_pattern(
        pattern_id="PAT-TEMP-001",
        operator_id="operator-darius",
        observation="Temporary test setting.",
        hypothesis="Temporary hypothesis.",
    )

    retired = engine.retire_pattern("PAT-TEMP-001", reason="Temporary test completed.")
    assert retired.status == PatternStatus.RETIRED
    assert retired.confidence_score == 0.0


def test_receipt_tampering_detection():
    engine = GovernedCollaborationMemoryEngine("407f7b52b161c520688bd8eef509146d86717c74")
    engine.observe_pattern("PAT-TAMPER-001", "op1", "obs", "hyp")

    receipt = engine.receipts[0]
    assert receipt.receipt_hash == receipt.compute_hash()

    # Tamper with exact_head_sha
    receipt.exact_head_sha = "tampered_sha"
    assert receipt.receipt_hash != receipt.compute_hash(), "Tampered receipt hash must mismatch."
