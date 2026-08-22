"""Digest-verified cognitive state persistence with fail-closed rehydration."""
from __future__ import annotations
import hashlib,json,os,tempfile
from pathlib import Path
from .state_schema import CognitiveState
class CognitivePersistenceError(ValueError): pass

def _canonical(state): return json.dumps(state.model_dump(mode='json'),sort_keys=True,separators=(',',':'))
def persist(path:str|Path,state:CognitiveState)->str:
    payload=_canonical(state); digest=hashlib.sha256(payload.encode()).hexdigest(); record=json.dumps({'payload':json.loads(payload),'digest':digest},sort_keys=True,separators=(',',':'))
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=target.parent,prefix='.cognitive-',text=True)
    try:
        with os.fdopen(fd,'w') as f: f.write(record); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,target)
    except Exception:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
    return digest

def rehydrate(path:str|Path)->CognitiveState:
    try: record=json.loads(Path(path).read_text())
    except Exception as e: raise CognitivePersistenceError('UNREADABLE_STATE') from e
    if not isinstance(record,dict) or set(record)!={'payload','digest'}: raise CognitivePersistenceError('MALFORMED_STATE')
    payload=json.dumps(record['payload'],sort_keys=True,separators=(',',':'))
    if hashlib.sha256(payload.encode()).hexdigest()!=record['digest']: raise CognitivePersistenceError('DIGEST_MISMATCH')
    try: return CognitiveState.model_validate(record['payload'])
    except Exception as e: raise CognitivePersistenceError('INVALID_SCHEMA') from e
