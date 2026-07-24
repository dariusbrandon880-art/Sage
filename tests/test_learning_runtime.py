"""SAGE Learning Runtime Layer - Integration and Governed Loop Tests."""

import pytest
from pathlib import Path
from sage.runtime import SAGERuntime
from sage.learning import KnowledgeCandidate, GovernedLearningLoop


@pytest.fixture
def clean_runtime(tmp_path):
    """Fixture to provide a clean SAGERuntime instance with temporary paths."""
    runtime = SAGERuntime(workspace_path=str(tmp_path))
    runtime.start()
    yield runtime
    runtime.stop()


def test_learning_candidate_creation(clean_runtime):
    """Scenario 1: Verify learned candidate creation and metadata preservation."""
    loop = GovernedLearningLoop(clean_runtime)

    fact_data = {
        "type": "design_pattern",
        "name": "Micro-kernel Security Pattern",
        "reusable": True,
        "evidence": ["sec_doc_001"]
    }

    candidate = loop.intake.ingest_fact(source="Security Reviewer", data=fact_data, confidence_score=0.7)

    assert candidate.candidate_id.startswith("cand_")
    assert candidate.source_reference == "Security Reviewer"
    assert candidate.knowledge_type == "design_pattern"
    assert candidate.confidence_score == 0.7
    assert "sec_doc_001" in candidate.evidence_links
    assert candidate.content["name"] == "Micro-kernel Security Pattern"


def test_spek_validation_routing(clean_runtime):
    """Scenario 2: Verify that an approved candidate is successfully routed through validation and promoted."""
    loop = GovernedLearningLoop(clean_runtime)

    raw_cand_id = "cand_encryption_rule"
    pattern_cand_id = f"pattern_{raw_cand_id}"

    rule_content = {
        "candidate_id": pattern_cand_id,
        "type": "rule_candidate",
        "name": "Encryption Standard Rule",
        "rule_body": "Force AES-256 for all persistent files",
        "reusable": True,
        "evidence": ["enc_check_1"]
    }

    from sage.acr.attestation import AttestationProvider
    provider = AttestationProvider(provider_type="TPM")
    signature = provider.sign_payload(rule_content)

    fact_data = {
        "candidate_id": raw_cand_id,
        "type": "rule_candidate",
        "name": "Encryption Standard Rule",
        "rule_body": "Force AES-256 for all persistent files",
        "signature": signature,
        "reusable": True,
        "evidence": ["enc_check_1"]
    }

    results = loop.process_incoming_event(source="Security Reviewer", event_data=fact_data, initial_confidence=0.85)

    assert len(results) == 1
    assert results[0]["approved"] is True
    assert results[0]["validation_state"] == "APPROVED"
    assert results[0]["promotion_status"] == "PROMOTED"

    archive_entries = clean_runtime.archive.list_all()
    assert len(archive_entries) == 1
    assert pattern_cand_id in archive_entries[0].title


def test_rejected_knowledge(clean_runtime):
    """Scenario 3: Verify that failed/untrusted candidates are rejected and not promoted."""
    loop = GovernedLearningLoop(clean_runtime)

    fact_data_low_conf = {
        "type": "design_pattern",
        "name": "Low Confidence Code Smell",
        "reusable": True,
    }
    results = loop.process_incoming_event(source="Reviewer", event_data=fact_data_low_conf, initial_confidence=0.5)

    assert len(results) == 1
    assert results[0]["approved"] is False
    assert results[0]["validation_state"] == "REJECTED"
    assert results[0]["promotion_status"] == "ABORTED"
    assert "Rejected" in results[0]["message"]

    fact_data_no_sig = {
        "type": "rule_candidate",
        "name": "Unsigned Dangerous Rule",
        "reusable": True,
    }
    results_no_sig = loop.process_incoming_event(source="Reviewer", event_data=fact_data_no_sig, initial_confidence=0.9)

    assert len(results_no_sig) == 1
    assert results_no_sig[0]["approved"] is False
    assert results_no_sig[0]["validation_state"] == "REJECTED"
    assert "SAGE-RT-KL-002" in results_no_sig[0]["message"] or "validation" in results_no_sig[0]["message"].lower() or "SAGE SPEK Validation" in results_no_sig[0]["message"]


def test_restart_continuity(clean_runtime, tmp_path):
    """Scenario 4: Verify learned state successfully survives restart."""
    loop = GovernedLearningLoop(clean_runtime)

    fact_data = {
        "type": "design_pattern",
        "name": "State Recovery Pattern",
        "pattern": True,
        "reusable": True,
    }
    results = loop.process_incoming_event(source="Reviewer", event_data=fact_data, initial_confidence=0.9)
    print("RESULTS:", results)

    assert len(results) == 1
    assert results[0]["approved"] is True

    clean_runtime.stop()

    fresh_runtime = SAGERuntime(workspace_path=str(tmp_path))
    fresh_runtime.start()

    fresh_loop = GovernedLearningLoop(fresh_runtime)

    assert len(fresh_loop.candidates) == 2
    rehydrated_pattern = None
    for cand in fresh_loop.candidates.values():
        if cand.candidate_id.startswith("pattern_"):
            rehydrated_pattern = cand
            break

    assert rehydrated_pattern is not None
    assert rehydrated_pattern.content["name"] == "State Recovery Pattern"
    assert rehydrated_pattern.validation_state == "APPROVED"
    assert rehydrated_pattern.promotion_status == "PROMOTED"

    fresh_runtime.stop()
