import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import hmac
import json

from sage.lab.index_layer_v0_1.provenance import ProvenanceRecord

class DocumentIndexer:
    """Handles tracking, hashing, metadata extraction, and indexing of markdown documents."""

    def __init__(self, workspace_root: str, author_node: str = "Jules"):
        self.workspace_root = Path(workspace_root)
        self.author_node = author_node
        self.records: Dict[str, ProvenanceRecord] = {}
        self.evidence_log_path = self.workspace_root / "sage_data" / "compliance" / "index_layer_v0_1_evidence.jsonl"

    def calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file's content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def generate_hmac_signature(self, record_data: dict) -> str:
        """Generate a secure signature using the record attributes."""
        # Use a stable serialization format
        serialized = json.dumps(record_data, sort_keys=True)
        key = b"SAGE-INDEX-SECRET-KEY-2026"
        return hmac.new(key, serialized.encode("utf-8"), hashlib.sha256).hexdigest()

    def index_document(
        self,
        file_relative_path: str,
        doc_id: str,
        title: str,
        doc_type: str = "markdown",
        parents: Optional[List[str]] = None,
        lifecycle_state: str = "PROPOSED"
    ) -> ProvenanceRecord:
        """Index a workspace document, validating it against the provenance schema."""
        full_path = self.workspace_root / file_relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Document file does not exist: {file_relative_path}")

        file_hash = self.calculate_hash(full_path)
        timestamp = datetime.now(timezone.utc)

        # Build initial dictionary to sign
        record_dict = {
            "doc_id": doc_id,
            "title": title,
            "doc_type": doc_type,
            "hash": file_hash,
            "parents": parents or [],
            "lifecycle_state": lifecycle_state,
            "author": self.author_node,
            "timestamp": timestamp.isoformat()
        }

        signature = self.generate_hmac_signature(record_dict)

        # Instantiate Pydantic model
        record = ProvenanceRecord(
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            hash=file_hash,
            parents=parents or [],
            lifecycle_state=lifecycle_state,
            author=self.author_node,
            timestamp=timestamp,
            signature=signature
        )

        self.records[doc_id] = record
        self.write_evidence_log(record)
        return record

    def write_evidence_log(self, record: ProvenanceRecord):
        """Auto-Logger Pipeline: Log index transactions to a tamper-evident compliance log."""
        # Ensure parent directories exist
        self.evidence_log_path.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "event_type": "DOCUMENT_INDEXED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "record": record.model_dump(mode="json")
        }

        with open(self.evidence_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
