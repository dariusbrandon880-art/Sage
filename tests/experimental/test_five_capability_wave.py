from sage.experimental.frontier_tree import FrontierNode, FrontierTree, KnowledgeStatus
from sage.experimental.frontier_portfolio import select_complementary_five
from sage.experimental.pfc_decision_engine import PFCDecisionEngine
from sage.experimental.temporal_research_memory import TemporalResearchMemory
from sage.experimental.observation_learning import observe
from sage.experimental.frontier_feedback import FeedbackOutcome


def test_frontier_and_portfolio_select_five():
    nodes=[FrontierNode(f"n{i}",f"node-{i}",KnowledgeStatus.KNOWN,(f"e{i}",),information_gain=i) for i in range(5)]
    tree=FrontierTree(nodes)
    flights=select_complementary_five(tree)
    assert len(flights)==5


def test_pfc_is_deterministic_and_fail_closed():
    engine=PFCDecisionEngine()
    state={"validated":True,"evidence_complete":True,"regression_free":True,"authorized":True,"evidence_refs":["e1"]}
    assert engine.decide(state)==engine.decide(state)
    state["regression_free"]=False
    assert engine.decide(state).action=="STOP"


def test_temporal_memory_compares_snapshots():
    memory=TemporalResearchMemory()
    memory.record("s1","t1",{"x":1},("e1",))
    memory.record("s2","t2",{"x":2,"y":3},("e2",))
    assert memory.compare("s1","s2")=={"x":(1,2),"y":(None,3)}


def test_observation_becomes_governed_learning_candidate():
    candidate=observe("n1",FeedbackOutcome.NEGATIVE_RESULT,"receipt-1")
    assert candidate.outcome=="FORBIDDEN_REGRESSION"
    assert candidate.next_action=="BLOCK"
