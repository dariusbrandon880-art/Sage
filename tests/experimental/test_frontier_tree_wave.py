from sage.experimental.frontier_tree import FrontierNode, FrontierTree
from sage.experimental.frontier_portfolio import select_complementary_five
from sage.experimental.frontier_discovery import DiscoveryCandidate, DiscoveryKind, admit


def test_tree_selects_exactly_five_distinct_nodes():
    tree = FrontierTree()
    for index in range(5):
        tree.add(FrontierNode(node_id=f"n{index}", priority=5-index, provenance=("evidence",)))
    flights = select_complementary_five(tree)
    assert len(flights) == 5
    assert len({flight.node_id for flight in flights}) == 5


def test_discovery_requires_provenance_and_challenge():
    candidate = DiscoveryCandidate("x", "bounded claim", DiscoveryKind.HYPOTHESIZED, ("source",), "CHALLENGED")
    assert admit(candidate) is candidate
