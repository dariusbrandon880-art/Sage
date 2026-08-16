"""SAGI State & Identity Anchor Module.

Implements Ω state initialization, immutable I(t0) identity anchor,
and cryptographic SHA-256 state tracking for the SAGI core simulator.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IdentityAnchor(BaseModel):
    """Immutable I(t0) identity anchor for SAGI governance."""
    initial_sha256: str
    genesis_timestamp: float = Field(default_factory=time.time)
    governance_version: str = "SAGI-v1.0.0"
    core_rules: List[str] = Field(
        default_factory=lambda: [
            "IDENTITY_INVARIANT_PRESERVED",
            "CRPL_F1_METADATA_NON_INFLUENCE",
            "CRPL_F2_PERSONA_NON_INFLUENCE",
            "BOUNDED_EVOLUTION_REGULATION"
        ]
    )


class SAGIState(BaseModel):
    """Omega (Ω) state representation for SAGI Digital Twin Brain."""
    state_id: str
    cycle_index: int = 0
    temperature: float = 0.7
    mutation_radius: float = 0.1
    active_hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    failure_memory: List[Dict[str, Any]] = Field(default_factory=list)
    identity_anchor: IdentityAnchor
    current_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.current_hash:
            self.current_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Compute deterministic SHA-256 checksum of state Ω."""
        payload = {
            "state_id": self.state_id,
            "cycle_index": self.cycle_index,
            "temperature": round(self.temperature, 4),
            "mutation_radius": round(self.mutation_radius, 4),
            "active_hypotheses": self.active_hypotheses,
            "failure_memory_count": len(self.failure_memory),
            "identity_anchor": self.identity_anchor.initial_sha256
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def update_hash(self) -> str:
        """Recalculate and update current_hash."""
        self.current_hash = self.compute_sha256()
        return self.current_hash

    @classmethod
    def initialize_genesis(cls, state_id: str = "sagi_genesis_omega") -> "SAGIState":
        """Initialize genesis Ω state with immutable I(t0) anchor."""
        seed_data = f"SAGI_GENESIS_I_T0:{state_id}:{time.time()}"
        initial_sha = hashlib.sha256(seed_data.encode("utf-8")).hexdigest()
        anchor = IdentityAnchor(initial_sha256=initial_sha)

        state = cls(
            state_id=state_id,
            cycle_index=0,
            temperature=0.7,
            mutation_radius=0.1,
            identity_anchor=anchor
        )
        state.update_hash()
        return state
