"""Governed complementary portfolio selection over the Frontier Tree."""
from __future__ import annotations
from dataclasses import dataclass
from .frontier_tree import FrontierTree
@dataclass(frozen=True)
class PortfolioFlight:
    role:str; node_id:str
ROLES=("consequential","information_gain","falsification","recovery","transfer")
def select_complementary_five(tree:FrontierTree)->tuple[PortfolioFlight,...]:
    portfolio=tree.select_five()
    if len(portfolio.node_ids)!=5 or len(set(portfolio.node_ids))!=5: raise ValueError("INVALID_FIVE_FLIGHT_PORTFOLIO")
    return tuple(PortfolioFlight(role,node_id) for role,node_id in zip(ROLES,portfolio.node_ids))
