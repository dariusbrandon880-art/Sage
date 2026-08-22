import pytest
from sage.experimental.frontier_tree import FrontierNode, FrontierTree, KnowledgeStatus
from sage.experimental.frontier_portfolio import select_complementary_five
from sage.experimental.frontier_discovery import DiscoveryCandidate, DiscoveryKind, admit
from sage.experimental.frontier_feedback import FrontierFeedback, FeedbackOutcome, classify_feedback


def node(i, **scores):
    return FrontierNode(node_id=f"n{i}", title=f"N{i}", status=KnowledgeStatus.HYPOTHESIZED, evidence_refs=(f"e{i}",), **scores)


def test_integrated_wave_selects_exactly_five_distinct_nodes():
    tree=FrontierTree([node(i, consequence=10-i) for i in range(5)])
    flights=select_complementary_five(tree)
    assert len(flights)==5
    assert len({f.node_id for f in flights})==5


def test_discovery_requires_provenance_and_challenge():
    candidate=DiscoveryCandidate("x","claim",DiscoveryKind.HYPOTHESIZED,("source",),"CHALLENGED")
    assert admit(candidate) is candidate
    with pytest.raises(ValueError):
        admit(DiscoveryCandidate("bad","claim",DiscoveryKind.HYPOTHESIZED,(),"OPEN"))


def test_negative_and_hold_feedback_remain_non_authoritative():
    assert classify_feedback(FrontierFeedback("n",FeedbackOutcome.NEGATIVE_RESULT,"ev"))=="FORBIDDEN_REGRESSION"
    assert classify_feedback(FrontierFeedback("n",FeedbackOutcome.HOLD,"ev"))=="UNRESOLVED"


def test_missing_feedback_provenance_fails_closed():
    with pytest.raises(ValueError):
        classify_feedback(FrontierFeedback("n",FeedbackOutcome.PASS,""))


def test_dependency_cycle_rejected():
    a=node(1, dependencies=("n2",)); b=node(2, dependencies=("n1",))
    with pytest.raises(ValueError, match="DEPENDENCY_CYCLE"):
        FrontierTree([a,b])
