import pytest
from sage.experimental.cognitive.research_bridge import ResearchNode,integrate,ResearchBridgeError

def test_valid_and_negative_projection():
 f,b,r=integrate((ResearchNode('a','fact',('e',),True),ResearchNode('b','bad',('e2',),True,True)))
 assert len(f)==1 and len(b)==1 and r.accepted==('a','b')
def test_unvalidated_rejected():
 f,b,r=integrate((ResearchNode('x','x',('e',),False),)); assert not f and r.rejected==('x',)
def test_missing_provenance_rejected():
 _,_,r=integrate((ResearchNode('x','x',(),True),)); assert r.rejected==('x',)
def test_duplicate_fails_closed():
 with pytest.raises(ResearchBridgeError): integrate((ResearchNode('x','x',('e',),True),ResearchNode('x','y',('e',),True)))
def test_deterministic_receipt():
 n=(ResearchNode('a','fact',('e',),True),); assert integrate(n)[2].digest==integrate(n)[2].digest
