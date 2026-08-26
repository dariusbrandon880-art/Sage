"""Deterministic selection of consequential capability frontiers."""
from __future__ import annotations
from typing import List, Tuple
from sage.capability_registry import SAGECapability
_STATUS_SCORE={"READY_FRONTIER":5,"PARTIAL":4,"BLOCKED":3,"RESEARCH_ONLY":2,"ACTIVE":1,"DEPRECATED":0}
def rank_frontiers(capabilities:List[SAGECapability],limit:int=5)->List[Tuple[str,int]]:
    candidates=[cap for cap in capabilities if cap.lifecycle_status in {"READY_FRONTIER","PARTIAL","BLOCKED","RESEARCH_ONLY"} or cap.validation_status!="VALIDATED"]
    scored=[]
    for cap in candidates:
        score=_STATUS_SCORE.get(cap.lifecycle_status,0)+min(len(cap.dependencies),3)+(1 if cap.incompletion_reason else 0)
        scored.append((cap.capability_id,score))
    return sorted(scored,key=lambda item:(-item[1],item[0]))[:limit]
