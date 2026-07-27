from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List

class ProvenanceRecord(BaseModel):
    """Provenance record tracking document lifecycle state and authenticity."""
    doc_id: str
    title: str
    doc_type: str  # doc, sheet, slide, drive_file, markdown
    hash: str
    parents: List[str] = Field(default_factory=list)
    lifecycle_state: str  # PROPOSED, VALIDATED, ARCHIVE_CANDIDATE, CANONICAL
    author: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signature: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "doc_id": "doc_001",
                    "title": "SAGE Constitution",
                    "doc_type": "markdown",
                    "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "parents": [],
                    "lifecycle_state": "CANONICAL",
                    "author": "GoogleAI",
                    "timestamp": "2026-07-27T13:45:00Z",
                    "signature": "SHA256-HMAC-SAGE-OK"
                }
            ]
        }
    }
