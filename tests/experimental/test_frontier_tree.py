import pytest
from sage.experimental.frontier_tree import FrontierNode, FrontierTree, KnowledgeStatus

def node(i, **kw):
    return FrontierNode(node_id=i,title=i,status=KnowledgeStatus.HYPOTHESIZED,evidence_refs=(f'e:{i}',),information_gain=1,**kw)

def test_selects_exactly_five_deterministically():
    tree=FrontierTree([node(str(i)) for i in range(6)])
    assert tree.select_five().node_ids==('0','1','2','3','4')

def test_rejects_missing_provenance():
    with pytest.raises(ValueError,match='MISSING_PROVENANCE'):
        FrontierTree([FrontierNode('x','x',KnowledgeStatus.KNOWN)])

def test_rejects_dependency_cycle():
    with pytest.raises(ValueError,match='DEPENDENCY_CYCLE'):
        FrontierTree([node('a',dependencies=('b',)),node('b',dependencies=('a',))])

def test_rejects_insufficient_admissible_frontiers():
    with pytest.raises(ValueError,match='INSUFFICIENT_ADMISSIBLE'):
        FrontierTree([node(str(i)) for i in range(4)]).select_five()
