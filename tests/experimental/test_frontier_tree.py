import pytest
from sage.experimental.frontier_tree import *
def node(i,**k):
 d=dict(node_id=i,title=i,status=KnowledgeStatus.HYPOTHESIZED,evidence_refs=('e',),information_gain=1,consequence=1);d.update(k);return FrontierNode(**d)
def test_exact_five(): assert len(FrontierTree(node(str(i)) for i in range(5)).select_five().node_ids)==5
def test_missing_provenance():
 with pytest.raises(ValueError,match='MISSING_PROVENANCE'): FrontierTree((node('a',evidence_refs=()),))
def test_cycle():
 with pytest.raises(ValueError,match='DEPENDENCY_CYCLE'): FrontierTree((node('a',dependencies=('b',)),node('b',dependencies=('a',))))
def test_insufficient():
 with pytest.raises(ValueError,match='INSUFFICIENT'): FrontierTree(node(str(i)) for i in range(4)).select_five()
def test_deterministic():
 t=FrontierTree(node(str(i)) for i in range(5));assert t.select_five()==t.select_five()
