from typing import Dict, Any, List
from pydantic import BaseModel, Field

class StateTransitionPayload(BaseModel):
    """Represents the structured transition envelope validated by CIV."""
    tx_id: str
    auth_token: str
    identity_ref: str
    target_state: str
    evidence_refs: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)
