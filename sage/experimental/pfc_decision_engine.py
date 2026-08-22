"""Deterministic executive decision projection over validated evidence."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Mapping, Any

@dataclass(frozen=True)
class Decision:
    action: str
    rationale_refs: tuple[str, ...]
    state_hash: str

class PFCDecisionEngine:
    """Pure decision layer; it recommends and records, but never authorizes execution."""
    ACTIONS=("HOLD","BUILD","STOP","AUTHORIZE")
    def decide(self, evidence: Mapping[str, Any]) -> Decision:
        required=("validated","evidence_complete","regression_free","authorized")
        if any(k not in evidence for k in required):
            raise ValueError("INCOMPLETE_DECISION_STATE")
        if not evidence["validated"] or not evidence["evidence_complete"]: action="HOLD"
        elif evidence["regression_free"] is False: action="STOP"
        elif evidence["authorized"]: action="AUTHORIZE"
        else: action="BUILD"
        payload=json.dumps(dict(evidence),sort_keys=True,separators=(",",":"),default=str)
        return Decision(action,tuple(evidence.get("evidence_refs",())),hashlib.sha256(payload.encode()).hexdigest())
