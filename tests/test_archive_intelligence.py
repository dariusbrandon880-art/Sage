"""Tests for SAGE Master Archive Intelligence layer."""

import pytest
import tempfile
from pathlib import Path

from sage.models import MemoryObject, ConfidenceLevel, ArchiveEntry
from sage.archive import Archive
from sage.validation import ValidationSystem
from sage.memory import Memory


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_archive_intelligence_automatic_promotion(temp_workspace):
    """Test that ValidationSystem automatically establishes intelligence metadata during promotion."""
    memory_store = Memory(str(temp_workspace / "memory"))
    archive_store = Archive(str(temp_workspace / "archive"))
    validation = ValidationSystem(memory_store, archive_store)

    # 1. Create a memory object with custom content
    obj = MemoryObject(
        object_type="architectural_decision",
        content={
            "title": "Adopt Event Sourcing",
            "source": "RFC-204",
            "decisions": ["dec_101"],
            "archive": True,
        },
        tags=["pattern", "event-sourcing"],
        confidence=ConfidenceLevel.VALIDATED,
    )
    memory_store.store(obj)

    # 2. Promote to Master Archive
    success, archive_id = validation.promote_to_archive(obj.id, "Validated RFC-204 Pattern")
    assert success is True

    # 3. Retrieve and assert intelligence properties
    entry = archive_store.retrieve_entry(archive_id)
    assert entry is not None
    assert entry.intelligence is not None

    # Lineage check
    lineage = entry.intelligence.lineage
    assert lineage is not None
    assert lineage.source == "RFC-204"
    assert "dec_101" in lineage.dependent_decisions
    assert lineage.validation_record is not None
    assert lineage.validation_record.success is True
    assert "non_empty_content" in lineage.validation_record.rules_applied

    # Confidence check
    confidence = entry.intelligence.confidence
    assert confidence is not None
    assert confidence.confidence_level == 1.0
    assert confidence.validation_status == "validated"
    assert obj.id in confidence.evidence_references
    assert len(confidence.review_history) == 1
    assert confidence.review_history[0].reviewer == "ValidationSystem"


def test_archive_intelligence_manual_updates(temp_workspace):
    """Test explicit/manual assignment of lineage, relationships, confidence, and decisions."""
    archive_store = Archive(str(temp_workspace / "archive"))

    # Create dummy entries
    entry_a = ArchiveEntry(
        id="archive_node_a",
        title="Database Schema Definition",
        tags=["database"],
        content={"driver": "postgresql"},
    )
    entry_b = ArchiveEntry(
        id="archive_node_b",
        title="Query Optimization Rules",
        tags=["database", "performance"],
        content={"index": "btree"},
    )

    archive_store.promote_to_archive(entry_a)
    archive_store.promote_to_archive(entry_b)

    # 1. Test Lineage Update
    archive_store.set_entry_lineage(
        entry_id="archive_node_a",
        source="System DB Spec v2",
        validation_rules=["custom_schema_check"],
        dependent_decisions=["dec_database_selection"],
    )

    reloaded_a = archive_store.retrieve_entry("archive_node_a")
    assert reloaded_a.intelligence.lineage.source == "System DB Spec v2"
    assert "dec_database_selection" in reloaded_a.intelligence.lineage.dependent_decisions
    assert reloaded_a.intelligence.lineage.validation_record.rules_applied == [
        "custom_schema_check"
    ]

    # 2. Test Relationship Update (add relationship: entry_b depends_on entry_a)
    archive_store.add_entry_relationship(
        source_id="archive_node_b",
        target_id="archive_node_a",
        relationship_type="depends_on",
        metadata={"priority": "high"},
    )

    reloaded_b = archive_store.retrieve_entry("archive_node_b")
    relationships_b = reloaded_b.intelligence.relationships
    assert len(relationships_b) == 1
    assert relationships_b[0].source_id == "archive_node_b"
    assert relationships_b[0].target_id == "archive_node_a"
    assert relationships_b[0].relationship_type == "depends_on"
    assert relationships_b[0].metadata == {"priority": "high"}

    # Bidirectional consistency check on entry_a
    reloaded_a_after_rel = archive_store.retrieve_entry("archive_node_a")
    assert len(reloaded_a_after_rel.intelligence.relationships) == 1
    assert reloaded_a_after_rel.intelligence.relationships[0].source_id == "archive_node_b"
    assert reloaded_a_after_rel.intelligence.relationships[0].target_id == "archive_node_a"

    # 3. Test Confidence Update
    archive_store.set_entry_confidence(
        entry_id="archive_node_a",
        confidence_level=0.95,
        validation_status="manually_verified",
        evidence_references=["ev_benchmarks_01", "ev_benchmarks_02"],
        review_notes="Completed review on staging environment",
        reviewer="principal_engineer",
    )

    reloaded_a_conf = archive_store.retrieve_entry("archive_node_a")
    conf_tracker = reloaded_a_conf.intelligence.confidence
    assert conf_tracker.confidence_level == 0.95
    assert conf_tracker.validation_status == "manually_verified"
    assert "ev_benchmarks_01" in conf_tracker.evidence_references
    assert len(conf_tracker.review_history) == 1
    assert conf_tracker.review_history[0].reviewer == "principal_engineer"
    assert conf_tracker.review_history[0].notes == "Completed review on staging environment"

    # 4. Test Decision Connection
    archive_store.add_entry_decision(
        entry_id="archive_node_a",
        decision_id="dec_postgresql_choice",
        affected_components=["data_store_service", "migration_engine"],
        reasoning_reference="ADR-005",
        validation_outcome="approved",
        successor_decisions=["dec_aurora_postgres"],
    )

    reloaded_a_dec = archive_store.retrieve_entry("archive_node_a")
    assert "dec_postgresql_choice" in reloaded_a_dec.decision_history
    assert len(reloaded_a_dec.intelligence.decisions) == 1
    dec_conn = reloaded_a_dec.intelligence.decisions[0]
    assert dec_conn.decision_id == "dec_postgresql_choice"
    assert "data_store_service" in dec_conn.affected_components
    assert dec_conn.reasoning_reference == "ADR-005"
    assert dec_conn.validation_outcome == "approved"
    assert "dec_aurora_postgres" in dec_conn.successor_decisions


def test_knowledge_graph_traversal(temp_workspace):
    """Test compilation and traversal of the Knowledge Graph."""
    archive_store = Archive(str(temp_workspace / "archive"))

    # Establish nodes
    n1 = ArchiveEntry(id="n1", title="System Architecture Overview")
    n2 = ArchiveEntry(id="n2", title="Auth Implementation")
    n3 = ArchiveEntry(id="n3", title="OAuth Provider integration")

    archive_store.promote_to_archive(n1)
    archive_store.promote_to_archive(n2)
    archive_store.promote_to_archive(n3)

    # Establish relationships
    archive_store.add_entry_relationship("n2", "n1", "derived_from")
    archive_store.add_entry_relationship("n3", "n2", "depends_on")

    # Add decision link
    archive_store.add_entry_decision(
        entry_id="n2",
        decision_id="dec_jwt_auth",
        affected_components=["auth_api"],
        validation_outcome="validated",
    )

    # Compile Knowledge Graph
    graph = archive_store.get_knowledge_graph()
    assert len(graph.nodes) == 4  # n1, n2, n3, and decision_dec_jwt_auth
    assert "n1" in graph.nodes
    assert "n2" in graph.nodes
    assert "n3" in graph.nodes
    assert "decision_dec_jwt_auth" in graph.nodes

    # Traverse n2 relationships
    n2_relationships = graph.get_relationships_for_node("n2")
    assert len(n2_relationships) == 3

    # Related nodes to n2
    n2_related = graph.get_related_nodes("n2")
    assert "n1" in n2_related
    assert "n3" in n2_related
    assert "decision_dec_jwt_auth" in n2_related

    # Specific relationship traversal
    n2_derived = graph.get_related_nodes("n2", relationship_type="derived_from")
    assert "n1" in n2_derived
    assert "n3" not in n2_derived
