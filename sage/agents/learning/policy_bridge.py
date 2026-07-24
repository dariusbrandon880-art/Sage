"""SAGE Learning Runtime - Policy Bridge and Proposal Schema.

Governs the formatting of learning observations, generation of policy proposals,
and cryptographic validation of the SHA-256 evidence receipt chain.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PolicyProposal(BaseModel):
    """Pydantic model representing a learning-driven policy modification proposal."""

    proposal_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    target_component: str
    proposed_setting: str
    value: Any
    rationale: str
    observations_hash: str  # Hash of observations that led to this proposal
    previous_receipt_hash: Optional[str] = None  # Links to previous receipt in chain
    evidence_signature: Optional[str] = None  # Cryptographic receipt/signature


class PolicyProposalBridge:
    """Bridges runtime observations and policy proposal receipt chain formatting."""

    def __init__(self, previous_receipt_hash: Optional[str] = None):
        """Initialize the Policy Bridge with an optional pointer to the previous receipt."""
        self.previous_receipt_hash = previous_receipt_hash or "sage_learning_genesis_hash"

    def format_observations_hash(self, observations: Dict[str, Any]) -> str:
        """Deterministically hashes raw runtime observations using SHA-256."""
        observations_json = json.dumps(observations, sort_keys=True)
        return hashlib.sha256(observations_json.encode("utf-8")).hexdigest()

    def generate_proposal(
        self,
        proposal_id: str,
        target_component: str,
        proposed_setting: str,
        value: Any,
        rationale: str,
        observations: Dict[str, Any],
    ) -> PolicyProposal:
        """Constructs a raw PolicyProposal with observations hashed."""
        obs_hash = self.format_observations_hash(observations)

        return PolicyProposal(
            proposal_id=proposal_id,
            target_component=target_component,
            proposed_setting=proposed_setting,
            value=value,
            rationale=rationale,
            observations_hash=obs_hash,
            previous_receipt_hash=self.previous_receipt_hash,
        )

    def generate_sha256_evidence_receipt(self, proposal: PolicyProposal, signing_key: str) -> str:
        """Produces a deterministic, secure SHA-256 evidence hash of the entire proposal and signing key."""
        proposal_dict = proposal.model_dump()
        # Remove signature before hashing to ensure determinism
        proposal_dict.pop("evidence_signature", None)

        proposal_json = json.dumps(proposal_dict, sort_keys=True)

        # Combine the serialized proposal with the signing key for a cryptographic evidence chain
        hash_payload = f"{proposal_json}:{signing_key}"
        return hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()
