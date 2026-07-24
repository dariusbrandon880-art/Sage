"""SAGE ACR-X Memory Layer Models.

Provides four isolated memory layers and robust, immutable MemoryTokens
complete with structural entropy and cryptographic digests.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class STPMemoryLayer(str, Enum):
    """Four isolated memory layers of SAGE ACR-X C3S."""

    WORKING = "WORKING"
    EPISODIC = "EPISODIC"
    SEMANTIC = "SEMANTIC"
    PROCEDURAL = "PROCEDURAL"


class MemoryToken(BaseModel):
    """Immutable MemoryToken structure with identity, timestamp, digest, and entropy."""

    token_id: str = Field(default_factory=lambda: f"tok_{uuid.uuid4().hex[:8]}")
    layer: STPMemoryLayer
    content: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cryptographic_digest: str = ""
    structural_entropy: float = 0.0

    model_config = {
        "frozen": True,  # Ensures immutable token structure
    }

    @classmethod
    def create(cls, layer: STPMemoryLayer, content: dict[str, Any]) -> "MemoryToken":
        """Calculates digest and entropy before freezing and creating the token."""
        # Calculate digest
        serialized = json.dumps(content, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode()).hexdigest()

        # Calculate structural entropy (Shannon entropy of payload character distribution)
        entropy = 0.0
        if serialized:
            total_chars = len(serialized)
            char_counts: dict[str, int] = {}
            for char in serialized:
                char_counts[char] = char_counts.get(char, 0) + 1
            import math

            for count in char_counts.values():
                prob = count / total_chars
                entropy -= prob * math.log2(prob)

        return cls(
            layer=layer,
            content=content,
            cryptographic_digest=digest,
            structural_entropy=round(entropy, 4),
        )
