"""Unit tests for SAGE Evidence Lineage Index and Validation Traceability."""

import json
from pathlib import Path
from sage.experimental.evidence_lineage import (
    EvidenceLineageTracker,
    EvidenceLineageIndex,
    EvidenceLineageItem,
    EvidenceLineageRelation
)


def test_evidence_lineage_tracker_hash_calculation(tmp_path):
    """Verify that cryptographic SHA-256 is correctly calculated for audit integrity."""
    test_file = tmp_path / "sample_evidence.json"
    sample_data = {"test": True, "value": 42}
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(sample_data, f)

    tracker = EvidenceLineageTracker()
    calculated_hash = tracker.calculate_sha256(test_file)
    assert len(calculated_hash) == 64
    assert isinstance(calculated_hash, str)


def test_evidence_lineage_parsing_and_relationships(tmp_path):
    """Verify that metadata, capabilities, tests, and relationship links are parsed correctly."""
    evidence_dir = tmp_path / "evidence_capture"
    evidence_dir.mkdir()

    # Create mock cognitive kernel report
    cognitive_file = evidence_dir / "cognitive_kernel_foundation_report.json"
    cognitive_data = {
        "report_id": "cognitive_kernel_foundation_report",
        "timestamp": 1785936400.0,
        "phase": "Phase 0 SAGE Cognitive Kernel Foundation",
        "status": "VALIDATED"
    }
    with open(cognitive_file, "w", encoding="utf-8") as f:
        json.dump(cognitive_data, f)

    # Create mock chatgpt activation report
    chatgpt_file = evidence_dir / "chatgpt_live_runtime_production_activation.json"
    chatgpt_data = {
        "evaluation_id": "EVAL-OPENAI-LIVE-ABC123",
        "timestamp": 1785936450.0,
        "validation_result": {
            "status": "SUCCESS"
        }
    }
    with open(chatgpt_file, "w", encoding="utf-8") as f:
        json.dump(chatgpt_data, f)

    # Instantiate tracker and compile index
    tracker = EvidenceLineageTracker(evidence_dir=str(evidence_dir))
    index = tracker.compile_index()

    assert index.total_artifacts_indexed == 2
    assert "cognitive_kernel_foundation_report" in index.artifacts
    assert "EVAL-OPENAI-LIVE-ABC123" in index.artifacts

    # Assert Cognitive report details
    cognitive_item = index.artifacts["cognitive_kernel_foundation_report"]
    assert "Phase 0 SAGE Cognitive Kernel Foundation" in cognitive_item.capabilities_validated
    assert "tests/experimental/test_cognitive_kernel.py" in cognitive_item.test_suites_referenced
    assert cognitive_item.archive_promotion_status == "PROMOTED"

    # Assert ChatGPT report details and relationships
    chatgpt_item = index.artifacts["EVAL-OPENAI-LIVE-ABC123"]
    assert "SAGE Production OpenAI Runtime Activation" in chatgpt_item.capabilities_validated
    assert chatgpt_item.archive_promotion_status == "READY_FOR_PROMOTION"
    assert len(chatgpt_item.relationships) == 1
    assert chatgpt_item.relationships[0].target_artifact_id == "openai_runtime_live_connection"
    assert chatgpt_item.relationships[0].relationship_type == "peer_of"


def test_evidence_lineage_index_generation_and_saving(tmp_path):
    """Verify end-to-end generation and saving of the Evidence Lineage Index."""
    evidence_dir = tmp_path / "evidence_capture"
    evidence_dir.mkdir()

    # Create a basic sample evidence artifact
    sample_file = evidence_dir / "demo_launcher_evidence.json"
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump({"report_id": "demo_launcher_evidence", "status": "COMPLETED"}, f)

    tracker = EvidenceLineageTracker(evidence_dir=str(evidence_dir))
    out_path = tracker.generate_and_save()

    saved_file = Path(out_path)
    assert saved_file.exists()

    with open(saved_file, "r", encoding="utf-8") as f:
        saved_index = json.load(f)

    assert saved_index["total_artifacts_indexed"] == 1
    assert "demo_launcher_evidence" in saved_index["artifacts"]
    assert "SAGE Demo Launcher & Scenario Replay" in saved_index["capability_map"]
