import json,pytest
from sage.experimental.cognitive.persistence import persist,rehydrate,CognitivePersistenceError
from sage.experimental.cognitive.state_schema import *
def state(): return CognitiveState(agent_identity=CognitiveAgentIdentity(agent_id='a',name='n',role='r',authority_level='l',governance_tier='g'),active_mission=CognitiveActiveMission(mission_id='m',objective='o'),operator_constraints=CognitiveOperatorConstraints(),confidence_state=CognitiveConfidenceState(overall_confidence=1,last_updated=1))
def test_roundtrip(tmp_path):
 p=tmp_path/'s.json'; d=persist(p,state()); assert rehydrate(p).model_dump()==state().model_dump() and len(d)==64
def test_tamper_fails_closed(tmp_path):
 p=tmp_path/'s';persist(p,state());x=json.loads(p.read_text());x['payload']['active_mission']['objective']='x';p.write_text(json.dumps(x));
 with pytest.raises(CognitivePersistenceError,match='DIGEST_MISMATCH'): rehydrate(p)
def test_truncated_fails_closed(tmp_path):
 p=tmp_path/'s';p.write_text('{');
 with pytest.raises(CognitivePersistenceError,match='UNREADABLE_STATE'): rehydrate(p)
def test_deterministic_digest(tmp_path):
 assert persist(tmp_path/'a',state())==persist(tmp_path/'b',state())
