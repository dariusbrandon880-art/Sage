"""FastAPI runtime server for SAGE."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from sage.runtime import SAGERuntime
from sage.models import DecisionType, MemoryObject, ConfidenceLevel
from sage.validation import ValidationSystem

app = FastAPI(
    title="SAGE Runtime API",
    description="SAGE Autonomous Continuity Runtime API",
    version="0.1.0"
)

# Global runtime instance
runtime = SAGERuntime()
validation = ValidationSystem(runtime.memory, runtime.archive)


# Request/Response models
class ObjectiveRequest(BaseModel):
    objective: str


class TaskRequest(BaseModel):
    task: str


class DecisionRequest(BaseModel):
    decision_type: str
    description: str
    rationale: str
    evidence: Optional[List[str]] = None


class MemoryCreateRequest(BaseModel):
    object_type: str
    content: Dict[str, Any]
    tags: Optional[List[str]] = None
    confidence: Optional[str] = None


class ValidationRequest(BaseModel):
    memory_id: str


class ArchivePromotionRequest(BaseModel):
    memory_id: str
    title: str
    tags: Optional[List[str]] = None


# Health and Status endpoints
@app.get("/")
async def root():
    return {"status": "SAGE Runtime online", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "runtime": "active"}


@app.get("/status")
async def get_status():
    return runtime.get_status()


@app.get("/export")
async def export_state():
    return runtime.export_all()


# Objective endpoints
@app.post("/objective")
async def set_objective(req: ObjectiveRequest):
    session_id = runtime.set_objective(req.objective)
    return {
        "session_id": session_id,
        "objective": req.objective,
        "status": "active"
    }


@app.get("/objective")
async def get_objective():
    return {
        "objective": runtime.current_state.current_objective,
        "active_task": runtime.current_state.active_task
    }


# Task endpoints
@app.post("/task")
async def set_task(req: TaskRequest):
    session_id = runtime.set_task(req.task)
    return {
        "session_id": session_id,
        "task": req.task,
        "status": "active"
    }


@app.get("/task")
async def get_task():
    return {
        "active_task": runtime.current_state.active_task,
        "blockers": runtime.current_state.blockers,
        "dependencies": runtime.current_state.dependencies
    }


# Decision endpoints
@app.post("/decision")
async def record_decision(req: DecisionRequest):
    decision_id = runtime.decisions.record_decision(
        decision_type=DecisionType(req.decision_type),
        description=req.description,
        rationale=req.rationale,
        evidence=req.evidence
    )
    return {"decision_id": decision_id, "status": "recorded"}


@app.get("/decisions")
async def list_decisions():
    decisions = runtime.decisions.list_all()
    return {
        "count": len(decisions),
        "decisions": [d.model_dump() for d in decisions]
    }


@app.get("/decision/{decision_id}")
async def get_decision(decision_id: str):
    decision = runtime.decisions.retrieve_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision.model_dump()


# Memory endpoints
@app.post("/memory")
async def create_memory(req: MemoryCreateRequest):
    confidence = ConfidenceLevel(req.confidence) if req.confidence else ConfidenceLevel.HYPOTHESIS
    
    memory_obj = MemoryObject(
        object_type=req.object_type,
        content=req.content,
        tags=req.tags or [],
        confidence=confidence
    )
    
    memory_id = runtime.memory.store(memory_obj)
    return {"memory_id": memory_id, "status": "stored"}


@app.get("/memory")
async def list_memory():
    objects = runtime.memory.list_all()
    return {
        "count": len(objects),
        "memory_objects": [obj.model_dump() for obj in objects]
    }


@app.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    obj = runtime.memory.retrieve(memory_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Memory object not found")
    return obj.model_dump()


@app.get("/memory/search/tag/{tag}")
async def search_by_tag(tag: str):
    results = runtime.memory.search_by_tag(tag)
    return {
        "tag": tag,
        "count": len(results),
        "results": [obj.model_dump() for obj in results]
    }


@app.get("/memory/search/type/{object_type}")
async def search_by_type(object_type: str):
    results = runtime.memory.search_by_type(object_type)
    return {
        "object_type": object_type,
        "count": len(results),
        "results": [obj.model_dump() for obj in results]
    }


# Archive endpoints
@app.get("/archive")
async def list_archive():
    entries = runtime.archive.list_all()
    return {
        "count": len(entries),
        "entries": [entry.model_dump() for entry in entries]
    }


@app.get("/archive/{entry_id}")
async def get_archive_entry(entry_id: str):
    entry = runtime.archive.retrieve_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Archive entry not found")
    return entry.model_dump()


@app.get("/archive/search/title/{title}")
async def search_archive_by_title(title: str):
    results = runtime.archive.search_by_title(title)
    return {
        "title_search": title,
        "count": len(results),
        "results": [entry.model_dump() for entry in results]
    }


# Validation endpoints
@app.post("/validate")
async def validate_memory(req: ValidationRequest):
    is_valid, failed_rules = validation.validate_memory(req.memory_id)
    return {
        "memory_id": req.memory_id,
        "is_valid": is_valid,
        "failed_rules": failed_rules
    }


@app.post("/promote/validated")
async def promote_to_validated(req: ValidationRequest):
    success, msg = validation.promote_to_validated(req.memory_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"memory_id": req.memory_id, "message": msg}


@app.post("/promote/archive")
async def promote_to_archive(req: ArchivePromotionRequest):
    success, result = validation.promote_to_archive(
        req.memory_id,
        title=req.title,
        tags=req.tags
    )
    if not success:
        raise HTTPException(status_code=400, detail=result)
    return {"archive_id": result, "status": "promoted"}


# Blocker endpoints
@app.post("/blocker")
async def add_blocker(data: Dict[str, str]):
    blocker = data.get("blocker")
    if not blocker:
        raise HTTPException(status_code=400, detail="Blocker description required")
    runtime.add_blocker(blocker)
    return {"blocker": blocker, "status": "added"}


@app.delete("/blocker")
async def resolve_blocker(data: Dict[str, str]):
    blocker = data.get("blocker")
    if not blocker:
        raise HTTPException(status_code=400, detail="Blocker description required")
    runtime.resolve_blocker(blocker)
    return {"blocker": blocker, "status": "resolved"}


# Checkpoint endpoints
@app.post("/checkpoint")
async def create_checkpoint():
    checkpoint_id = runtime.checkpoint()
    return {"checkpoint_id": checkpoint_id, "status": "created"}


# Handoff and Restore endpoints
class RestoreRequest(BaseModel):
    handoff_file: str


@app.post("/handoff")
async def generate_handoff(file_path: Optional[str] = None):
    try:
        saved_path = runtime.generate_handoff(file_path)
        return {"status": "success", "handoff_file": saved_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate handoff: {str(e)}")


@app.post("/restore")
async def restore_session(req: RestoreRequest):
    success = runtime.restore_session(req.handoff_file)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to restore session from {req.handoff_file}")
    return {"status": "success", "message": f"Session restored from {req.handoff_file}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
