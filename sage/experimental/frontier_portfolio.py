"""Governed complementary portfolio selection over the Frontier Tree."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .frontier_tree import FrontierNode, FrontierTree


@dataclass(frozen=True)
class PortfolioFlight:
    role: str
    node_id: str


ROLES = ("consequential", "information_gain", "falsification", "recovery", "transfer")


def _admissible(tree: FrontierTree) -> list[FrontierNode]:
    return [node for node in tree.nodes() if node.provenance and not node.conflicts]


def select_complementary_five(tree: FrontierTree) -> tuple[PortfolioFlight, ...]:
    nodes = _admissible(tree)
    if len(nodes) < 5:
        raise ValueError("insufficient admissible frontier for governed five-flight wave")
    ordered = sorted(nodes, key=lambda node: (-node.priority, node.node_id))
    selected: list[PortfolioFlight] = []
    used: set[str] = set()
    for role, node in zip(ROLES, ordered):
        if node.node_id in used:
            raise ValueError("duplicate frontier selection")
        used.add(node.node_id)
        selected.append(PortfolioFlight(role=role, node_id=node.node_id))
    return tuple(selected)
