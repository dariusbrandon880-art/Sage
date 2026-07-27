import tempfile
from pathlib import Path
import pytest
import json
from datetime import datetime, timezone
from pydantic import ValidationError

from sage.lab.index_layer_v0_1.provenance import ProvenanceRecord
from sage.lab.index_layer_v0_1.indexing import DocumentIndexer
from sage.lab.index_layer_v0_1.mapping import ArchitectureMap

def test_architecture_tier_determination():
    """Verify that file paths are mapped to correct tiers."""
    arch_map = ArchitectureMap(workspace_root=".")

    assert arch_map.determine_file_tier("sage/runtime/engine.py") == "runtime"
    assert arch_map.determine_file_tier("sage/core/spek.py") == "core"
    assert arch_map.determine_file_tier("Main Archive/INDEX.md") == "archive"
    assert arch_map.determine_file_tier("sage/archive/core.py") == "archive"
    assert arch_map.determine_file_tier("sage/lab/index_layer_v0_1/mapping.py") == "lab"
    assert arch_map.determine_file_tier("scripts/production_check.py") == "external"


def test_one_way_import_law():
    """Verify that there are zero violations of the One-Way Import Law in production code."""
    arch_map = ArchitectureMap(workspace_root=".")
    is_compliant, violations = arch_map.verify_one_way_import_law()

    assert is_compliant, f"One-Way Import Law violations found: {violations}"
    assert len(violations) == 0


def test_one_way_import_law_violation_detection():
    """Verify that ArchitectureMap correctly flags illegal imports using AST analysis."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        # Create dummy structure
        runtime_dir = tmp_root / "sage" / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)

        # Write file with illegal import
        bad_file = runtime_dir / "bad_module.py"
        with open(bad_file, "w", encoding="utf-8") as f:
            f.write("import sage.lab.index_layer_v0_1\n")

        # Write another file with illegal import from
        bad_file_2 = runtime_dir / "bad_module_2.py"
        with open(bad_file_2, "w", encoding="utf-8") as f:
            f.write("from sage.evolution.something import x\n")

        arch_map = ArchitectureMap(workspace_root=str(tmp_root))
        is_compliant, violations = arch_map.verify_one_way_import_law()

        assert not is_compliant
        assert len(violations) == 2
        assert any("Illegal direct import 'sage.lab.index_layer_v0_1'" in v for v in violations)
        assert any("Illegal from-import from 'sage.evolution.something'" in v for v in violations)


def test_provenance_record_validation():
    """Verify that ProvenanceRecord parses valid input and flags invalid fields."""
    # Valid
    record = ProvenanceRecord(
        doc_id="doc_test",
        title="Test Document",
        doc_type="markdown",
        hash="f6c8e9f2a7d1c3b5a8f0e2d4c4a7b2e9c1f0d3a5",
        parents=["parent_doc"],
        lifecycle_state="PROPOSED",
        author="Jules",
        timestamp=datetime.now(timezone.utc),
        signature="test_signature"
    )
    assert record.doc_id == "doc_test"
    assert record.lifecycle_state == "PROPOSED"

    # Invalid doc_type is caught if type constraints fail or standard pydantic validation acts
    with pytest.raises(ValidationError):
        # We supply an invalid type for a field to trigger a validation error
        # e.g. timestamp must be datetime or compatible parseable string
        ProvenanceRecord(
            doc_id="doc_err",
            title="Test Error",
            doc_type="markdown",
            hash="abc",
            lifecycle_state="PROPOSED",
            author="Jules",
            timestamp="not-a-datetime",
            signature="test"
        )


def test_document_indexer_indexing():
    """Verify DocumentIndexer can hash, sign, index, and log document transactions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)

        # Create a test file
        test_file_rel = "docs/test_doc.md"
        test_file = tmp_root / test_file_rel
        test_file.parent.mkdir(parents=True, exist_ok=True)
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("# Hello SAGE\nThis is a temporary document.")

        indexer = DocumentIndexer(workspace_root=str(tmp_root), author_node="Jules")
        record = indexer.index_document(
            file_relative_path=test_file_rel,
            doc_id="doc_hello",
            title="Hello Document",
            doc_type="markdown",
            parents=[],
            lifecycle_state="VALIDATED"
        )

        # Verify fields
        assert record.doc_id == "doc_hello"
        assert record.title == "Hello Document"
        assert record.lifecycle_state == "VALIDATED"
        assert record.hash == indexer.calculate_hash(test_file)
        assert record.author == "Jules"
        assert record.signature != ""

        # Verify HMAC signature is deterministic and matches
        record_dict = {
            "doc_id": "doc_hello",
            "title": "Hello Document",
            "doc_type": "markdown",
            "hash": record.hash,
            "parents": [],
            "lifecycle_state": "VALIDATED",
            "author": "Jules",
            "timestamp": record.timestamp.isoformat()
        }
        expected_sig = indexer.generate_hmac_signature(record_dict)
        assert record.signature == expected_sig

        # Verify evidence logging
        evidence_file = tmp_root / "sage_data" / "compliance" / "index_layer_v0_1_evidence.jsonl"
        assert evidence_file.exists()

        with open(evidence_file, "r") as f:
            lines = f.readlines()

        assert len(lines) == 1
        log_data = json.loads(lines[0])
        assert log_data["event_type"] == "DOCUMENT_INDEXED"
        assert log_data["record"]["doc_id"] == "doc_hello"
        assert log_data["record"]["signature"] == record.signature
