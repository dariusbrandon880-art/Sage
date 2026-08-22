"""Read-only evidence-bounded frontier selection."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Iterable
class KnowledgeStatus(str, Enum): KNOWN="KNOWN"; TRANSFERRED="TRANSFERRED"; HYPOTHESIZED="HYPOTHESIZED"
@dataclass(frozen=True)
class FrontierNode:
    node_id: str; title: str; status: KnowledgeStatus; evidence_refs: tuple[str,...]=(); dependencies: tuple[str,...]=(); conflicts: tuple[str,...]=(); negative_refs: tuple[str,...]=(); information_gain: float=0.0; consequence: float=0.0; falsification: float=0.0; recovery: float=0.0; transfer: float=0.0
@dataclass(frozen=True)
class Portfolio: node_ids: tuple[str,...]; score: float
class FrontierTree:
    def __init__(self,nodes: Iterable[FrontierNode]):
        self.nodes={n.node_id:n for n in nodes}
        if not self.nodes: raise ValueError("EMPTY_FRONTIER")
        self._validate()
    def _validate(self):
        for n in self.nodes.values():
            if not n.evidence_refs: raise ValueError(f"MISSING_PROVENANCE:{n.node_id}")
            for d in n.dependencies:
                if d not in self.nodes: raise ValueError(f"MISSING_DEPENDENCY:{n.node_id}:{d}")
            for c in n.conflicts:
                if c not in self.nodes: raise ValueError(f"MISSING_CONFLICT:{n.node_id}:{c}")
        def visit(node,stack,seen):
            if node in stack: raise ValueError("DEPENDENCY_CYCLE")
            if node in seen:return
            seen.add(node)
            for d in self.nodes[node].dependencies: visit(d,stack|{node},seen)
        for n in self.nodes: visit(n,set(),set())
    def select_five(self)->Portfolio:
        ranked=sorted(((n.information_gain+n.consequence+n.falsification+n.recovery+n.transfer,n.node_id) for n in self.nodes.values()),key=lambda x:(-x[0],x[1]))
        chosen=[]
        for score,node_id in ranked:
            n=self.nodes[node_id]
            if len(chosen)==5: break
            if any(node_id in self.nodes[x].conflicts or x in n.conflicts for x in chosen): continue
            if all(d in chosen for d in n.dependencies): chosen.append(node_id)
        if len(chosen)!=5: raise ValueError("INSUFFICIENT_ADMISSIBLE_FRONTIERS")
        scores=dict(ranked)
        return Portfolio(tuple(chosen),sum(scores[x] for x in chosen))
