"""Governed Frontier Tree for evidence-bounded five-flight selection."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

class KnowledgeStatus(str, Enum):
    KNOWN="KNOWN"; TRANSFERRED="TRANSFERRED"; HYPOTHESIZED="HYPOTHESIZED"

@dataclass(frozen=True)
class FrontierNode:
    node_id: str
    title: str
    status: KnowledgeStatus
    evidence_refs: tuple[str,...]=()
    dependencies: tuple[str,...]=()
    conflicts: tuple[str,...]=()
    negative_refs: tuple[str,...]=()
    information_gain: float=0.0
    consequence: float=0.0
    falsification: float=0.0
    recovery: float=0.0
    transfer: float=0.0

@dataclass(frozen=True)
class Portfolio:
    node_ids: tuple[str,...]
    score: float

class FrontierTree:
    """Read-only frontier graph. Selection grants no execution or promotion authority."""
    def __init__(self, nodes: Iterable[FrontierNode]):
        self.nodes={n.node_id:n for n in nodes}
        if len(self.nodes)==0: raise ValueError("EMPTY_FRONTIER")
        self._validate()
    def _validate(self):
        for n in self.nodes.values():
            if not n.evidence_refs: raise ValueError(f"MISSING_PROVENANCE:{n.node_id}")
            for dep in n.dependencies:
                if dep not in self.nodes: raise ValueError(f"MISSING_DEPENDENCY:{n.node_id}:{dep}")
            for c in n.conflicts:
                if c not in self.nodes: raise ValueError(f"MISSING_CONFLICT:{n.node_id}:{c}")
        def visit(node, stack, seen):
            if node in stack: raise ValueError("DEPENDENCY_CYCLE")
            if node in seen: return
            seen.add(node)
            for dep in self.nodes[node].dependencies: visit(dep, stack|{node}, seen)
        for node in self.nodes: visit(node,set(),set())
    def select_five(self)->Portfolio:
        admissible=[]
        for n in self.nodes.values():
            if any(c in self.nodes for c in n.conflicts): continue
            score=n.information_gain+n.consequence+n.falsification+n.recovery+n.transfer
            admissible.append((score,n.node_id))
        admissible.sort(key=lambda x:(-x[0],x[1]))
        chosen=[]
        for score,node_id in admissible:
            n=self.nodes[node_id]
            if len(chosen)>=5: break
            if any(node_id in self.nodes[x].conflicts or x in n.conflicts for x in chosen): continue
            if all(dep in chosen or dep not in self.nodes for dep in n.dependencies): chosen.append(node_id)
        if len(chosen)!=5: raise ValueError("INSUFFICIENT_ADMISSIBLE_FRONTIERS")
        return Portfolio(tuple(chosen),sum(next(s for s,i in admissible if i==x) for x in chosen))
