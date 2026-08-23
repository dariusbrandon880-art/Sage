"""Bounded bridge from validated research records into cognitive projections."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .state_schema import CognitiveValidatedFact, CognitiveForbiddenRegression

class ResearchBridgeError(ValueError): pass
@dataclass(frozen=True)
class ResearchNode:
    node_id:str; statement:str; evidence_refs:tuple[str,...]; validated:bool; negative:bool=False
@dataclass(frozen=True)
class ResearchBridgeReceipt:
    accepted:tuple[str,...]; rejected:tuple[str,...]; digest:str

def integrate(nodes:tuple[ResearchNode,...]):
    seen=set(); facts=[]; forbidden=[]; accepted=[]; rejected=[]
    for n in nodes:
        if not n.node_id or n.node_id in seen: raise ResearchBridgeError('DUPLICATE_NODE')
        seen.add(n.node_id)
        if not n.validated or not n.evidence_refs or not n.statement.strip(): rejected.append(n.node_id); continue
        accepted.append(n.node_id)
        if n.negative:
            forbidden.append(CognitiveForbiddenRegression(regression_id=f'research-negative:{n.node_id}',description=n.statement,restricted_actions=list(n.evidence_refs),blocked_states=['AUTOMATIC_PROMOTION']))
        else:
            facts.append(CognitiveValidatedFact(fact_id=f'research:{n.node_id}',statement=n.statement,evidence_references=list(n.evidence_refs),confidence_score=1.0))
    payload={'accepted':sorted(accepted),'rejected':sorted(rejected)}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return tuple(facts),tuple(forbidden),ResearchBridgeReceipt(tuple(sorted(accepted)),tuple(sorted(rejected)),digest)
