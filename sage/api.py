"""FastAPI runtime server for SAGE with robust authentication boundaries and live webhook validation."""

import json
import hmac
import hashlib
import os
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from sage.runtime import (
    SAGERuntime,
    check_health,
    generate_diagnostic_report,
    generate_capability_report,
    get_metrics_collector,
)
from sage.models import DecisionType, MemoryObject, ConfidenceLevel, ExternalSessionPayload
from sage.validation import ValidationSystem
from sage.service import LifecycleManager
from sage.integration import (
    ChatGPTClient,
    GeminiJulesClient,
    ToolIntegrationManager,
    GoogleWorkspaceSyncManager,
    ConnectorRegistry,
    AIQueryRequest,
    GitHubEvent,
    GoogleWorkspaceArtifact,
)

app = FastAPI(
    title="SAGE Runtime API",
    description="SAGE Autonomous Continuity Runtime API with Live Webhooks",
    version="1.1.0",
)

# Global runtime instance
runtime = SAGERuntime()
runtime.start()
validation = ValidationSystem(runtime.memory, runtime.archive)

# Instantiate Service & Integration managers
lifecycle_mgr = LifecycleManager()
lifecycle_mgr.startup()  # Default startup on initialization
chatgpt_client = ChatGPTClient(runtime)
gemini_jules_client = GeminiJulesClient(runtime)
tool_mgr = ToolIntegrationManager(runtime)
workspace_sync_mgr = GoogleWorkspaceSyncManager(runtime)


# Global Middleware for SAGE API Key Authentication Boundaries
@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    require_auth = os.getenv("SAGE_REQUIRE_AUTH", "false").lower() == "true"

    # /system-frame is read-only but we can bypass or enforce depending on config.
    # The requirement: "Respect authentication boundaries."
    # So if SAGE_REQUIRE_AUTH is true, /system-frame should be protected.
    # Therefore, we remove '/system-frame' from the bypass list if SAGE_REQUIRE_AUTH is active.
    # Let's ensure /system-frame is NOT in the bypass list!
    bypass_paths_with_auth = ["/", "/health", "/docs", "/redoc", "/openapi.json"]

    if require_auth and request.url.path not in bypass_paths_with_auth:
        x_api_key = request.headers.get("x-api-key")
        if not x_api_key or not lifecycle_mgr.authorize(x_api_key):
            return JSONResponse(
                status_code=401, content={"detail": "Unauthorized: Invalid or missing API key."}
            )

    return await call_next(request)


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
    return {"status": "SAGE Runtime online", "version": "1.1.0"}


@app.get("/health")
async def health():
    return check_health(runtime)


@app.get("/status")
async def get_status():
    return runtime.get_status()


@app.get("/runtime/diagnostics")
async def get_runtime_diagnostics():
    return generate_diagnostic_report(runtime)


@app.get("/runtime/capabilities")
async def get_runtime_capabilities():
    return generate_capability_report(runtime)


@app.get("/runtime/metrics")
async def get_runtime_metrics():
    return get_metrics_collector().get_metrics()


@app.get("/export")
async def export_state():
    return runtime.export_all()


# System Frame endpoint (authorized read-only view of SAGE context)
@app.get("/system-frame")
async def get_system_frame():
    # Read raw contents of MASTER_SNAPSHOT.md and SESSION_STATE.md
    master_snapshot_path = Path("docs/master/MASTER_SNAPSHOT.md")
    session_state_path = Path("docs/master/SESSION_STATE.md")

    master_snapshot_content = ""
    if master_snapshot_path.exists():
        with open(master_snapshot_path, "r", encoding="utf-8") as f:
            master_snapshot_content = f.read()

    session_state_content = ""
    if session_state_path.exists():
        with open(session_state_path, "r", encoding="utf-8") as f:
            session_state_content = f.read()

    # Retrieve all structured state elements for automatic zero-copy platform rehydration
    active_objectives = (
        [runtime.current_state.current_objective] if runtime.current_state.current_objective else []
    )
    current_milestone = (
        "Milestone 3.3 - Universal SAGE Connector Layer fully integrated and validated"
    )
    active_task = runtime.current_state.active_task or "None"
    blockers = runtime.current_state.blockers or []

    # Decisions
    decisions = [d.model_dump() for d in runtime.decisions.list_all()]

    # Validated Knowledge (Memory Store with validated/archived confidence levels)
    validated_knowledge = [
        obj.model_dump()
        for obj in runtime.memory.list_all()
        if obj.confidence in [ConfidenceLevel.VALIDATED, ConfidenceLevel.ARCHIVED]
    ]

    # Master Archive References
    master_archive_references = [entry.model_dump() for entry in runtime.archive.list_all()]

    # Get connector availability from registry
    registry = ConnectorRegistry(runtime)
    connectors = [c.model_dump() for c in registry.get_all_connectors()]

    # Validated architecture summary
    architecture_summary = {
        "acr_bridge": "Session lineage and dependency graph tracking",
        "archive": "Master Archive validated knowledge engine and auditable logs",
        "memory": "Lab memory indexing and tag querying with high-performance key-value backend",
        "validation": "Multi-rule quality checker and promotion pipeline",
        "continuity_bridge": "Unified single-transaction ingestion, classification, and validation pathway",
    }

    frame = {
        "runtime_status": "active" if runtime.active else "inactive",
        "master_snapshot_markdown": master_snapshot_content,
        "session_state_markdown": session_state_content,
        "current_milestone": current_milestone,
        "active_objectives": active_objectives,
        "active_task": active_task,
        "blockers": blockers,
        "decisions": decisions,
        "validated_knowledge": validated_knowledge,
        "master_archive_references": master_archive_references,
        "validated_architecture_summary": architecture_summary,
        "connectors": connectors,
        "runtime_health": check_health(runtime),
    }
    return frame


# Objective endpoints
@app.post("/objective")
async def set_objective(req: ObjectiveRequest):
    session_id = runtime.set_objective(req.objective)
    return {"session_id": session_id, "objective": req.objective, "status": "active"}


@app.get("/objective")
async def get_objective():
    return {
        "objective": runtime.current_state.current_objective,
        "active_task": runtime.current_state.active_task,
    }


# Task endpoints
@app.post("/task")
async def set_task(req: TaskRequest):
    session_id = runtime.set_task(req.task)
    return {"session_id": session_id, "task": req.task, "status": "active"}


@app.get("/task")
async def get_task():
    return {
        "active_task": runtime.current_state.active_task,
        "blockers": runtime.current_state.blockers,
        "dependencies": runtime.current_state.dependencies,
    }


# Decision endpoints
@app.post("/decision")
async def record_decision(req: DecisionRequest):
    decision_id = runtime.decisions.record_decision(
        decision_type=DecisionType(req.decision_type),
        description=req.description,
        rationale=req.rationale,
        evidence=req.evidence,
    )
    return {"decision_id": decision_id, "status": "recorded"}


@app.get("/decisions")
async def list_decisions():
    decisions = runtime.decisions.list_all()
    return {"count": len(decisions), "decisions": [d.model_dump() for d in decisions]}


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
        object_type=req.object_type, content=req.content, tags=req.tags or [], confidence=confidence
    )

    memory_id = runtime.memory.store(memory_obj)
    return {"memory_id": memory_id, "status": "stored"}


@app.get("/memory")
async def list_memory():
    objects = runtime.memory.list_all()
    return {"count": len(objects), "memory_objects": [obj.model_dump() for obj in objects]}


@app.get("/memory/{memory_id}")
async def get_memory(memory_id: str):
    obj = runtime.memory.retrieve(memory_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Memory object not found")
    return obj.model_dump()


@app.get("/memory/search/tag/{tag}")
async def search_by_tag(tag: str):
    results = runtime.memory.search_by_tag(tag)
    return {"tag": tag, "count": len(results), "results": [obj.model_dump() for obj in results]}


@app.get("/memory/search/type/{object_type}")
async def search_by_type(object_type: str):
    results = runtime.memory.search_by_type(object_type)
    return {
        "object_type": object_type,
        "count": len(results),
        "results": [obj.model_dump() for obj in results],
    }


# Archive endpoints
@app.get("/archive")
async def list_archive():
    entries = runtime.archive.list_all()
    return {"count": len(entries), "entries": [entry.model_dump() for entry in entries]}


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
        "results": [entry.model_dump() for entry in results],
    }


# Validation endpoints
@app.post("/validate")
async def validate_memory(req: ValidationRequest):
    is_valid, failed_rules = validation.validate_memory(req.memory_id)
    return {"memory_id": req.memory_id, "is_valid": is_valid, "failed_rules": failed_rules}


@app.post("/promote/validated")
async def promote_to_validated(req: ValidationRequest):
    success, msg = validation.promote_to_validated(req.memory_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"memory_id": req.memory_id, "message": msg}


@app.post("/promote/archive")
async def promote_to_archive(req: ArchivePromotionRequest):
    session_state = None
    if runtime.context and runtime.context.session_id:
        session_state = runtime.session_manager.retrieve_session(runtime.context.session_id)

    success, result = validation.promote_to_archive(
        req.memory_id, title=req.title, tags=req.tags, session_state=session_state
    )
    if not success:
        raise HTTPException(status_code=400, detail=result)

    if session_state:
        runtime.session_manager.save_session(session_state)

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
        raise HTTPException(
            status_code=400, detail=f"Failed to restore session from {req.handoff_file}"
        )
    return {"status": "success", "message": f"Session restored from {req.handoff_file}"}


# Service lifecycle endpoints
@app.post("/service/startup")
async def service_startup(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or not lifecycle_mgr.authorize(x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return lifecycle_mgr.startup()


@app.post("/service/shutdown")
async def service_shutdown(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or not lifecycle_mgr.authorize(x_api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return lifecycle_mgr.shutdown()


@app.get("/service/diagnostics")
async def service_diagnostics():
    return lifecycle_mgr.get_diagnostics()


# AI query and continuation endpoints
@app.post("/ai/query/chatgpt")
async def ai_query_chatgpt(req: AIQueryRequest):
    return chatgpt_client.execute_query(req)


@app.post("/ai/query/gemini-jules")
async def ai_query_gemini_jules(req: AIQueryRequest):
    return gemini_jules_client.execute_query(req)


@app.get("/ai/context")
async def ai_context(prompt: str):
    return chatgpt_client.retrieve_context(prompt)


# Secure GitHub Webhook event ingestion endpoint with HMAC validation and raw payload support
@app.post("/tools/github/event")
async def index_github_event(request: Request):
    # 1. Signature validation
    body = await request.body()
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if webhook_secret:
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature or not signature.startswith("sha256="):
            raise HTTPException(
                status_code=401, detail="GitHub signature header missing or invalid."
            )
        expected_sig = signature.split("=")[1]
        mac = hmac.new(webhook_secret.encode(), msg=body, digestmod=hashlib.sha256)
        if not hmac.compare_digest(mac.hexdigest(), expected_sig):
            raise HTTPException(status_code=401, detail="GitHub signature verification failed.")

    # 2. Parse payload JSON
    try:
        data = json.loads(body) if body else {}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 3. Handle raw webhooks from GitHub or direct GitHubEvent models
    is_raw_gh = "repository" in data and (
        "pusher" in data or "sender" in data or "pull_request" in data
    )

    if is_raw_gh:
        # Extract metadata from raw GitHub structure
        event_type = request.headers.get("X-GitHub-Event", "push")
        repo_name = data.get("repository", {}).get("full_name", "unknown/repo")
        author = "unknown"
        if "sender" in data:
            author = data["sender"].get("login", "unknown")
        elif "pusher" in data:
            author = data["pusher"].get("name", "unknown")

        ref = data.get("ref")

        # Map directly to canonical GitHubEvent schema
        event = GitHubEvent(
            event_type=event_type, repository=repo_name, ref=ref, author=author, payload=data
        )
    else:
        # Standard repository payload validation
        try:
            event = GitHubEvent(**data)
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Unprocessable GitHubEvent payload: {str(e)}"
            )

    event_id = tool_mgr.index_github_event(event)
    return {"event_id": event_id, "status": "indexed"}


@app.post("/tools/workspace/artifact")
async def index_workspace_artifact(artifact: GoogleWorkspaceArtifact):
    artifact_id = tool_mgr.index_workspace_artifact(artifact)
    return {"doc_id": artifact_id, "status": "indexed"}


@app.get("/tools/index/relationships")
async def get_tool_relationships(query_tag: str):
    return tool_mgr.get_relationship_index(query_tag)


@app.post("/tools/workspace/sync")
async def sync_workspace(credentials_path: Optional[str] = None):
    try:
        result = workspace_sync_mgr.sync_to_google_workspace(credentials_path)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Google Workspace synchronization failed: {str(e)}"
        )


# Snapshot endpoints
@app.post("/snapshot")
async def create_snapshot():
    snapshot_id = runtime.checkpoint()
    return {"snapshot_id": snapshot_id, "status": "created"}


@app.get("/snapshots")
async def list_snapshots():
    workspace = runtime.workspace_path
    snapshots = []
    if workspace.exists():
        for path in workspace.glob("checkpoint_*.json"):
            snapshots.append(
                {
                    "snapshot_id": path.stem,
                    "file_path": str(path),
                    "size_bytes": path.stat().st_size,
                    "created_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                }
            )
    return {"count": len(snapshots), "snapshots": snapshots}


# Ingestion, reasoning, and self-verification endpoints
@app.post("/ingest")
async def ingest_payload(payload: ExternalSessionPayload):
    try:
        result = runtime.ingest_session_payload(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/reason")
async def reason_over_continuity():
    try:
        result = runtime.reason_over_continuity()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")


@app.get("/verify")
async def verify_integrity():
    try:
        result = runtime.verify_integrity()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Self-verification failed: {str(e)}")


# Continuity/Snapshot endpoints
@app.post("/continuity/snapshot")
async def create_continuity_snapshot():
    try:
        snapshot_id = runtime.create_workspace_snapshot()
        return {"status": "success", "snapshot_id": snapshot_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/continuity/snapshots")
async def list_continuity_snapshots():
    try:
        snapshots = runtime.list_workspace_snapshots()
        return {"snapshots": snapshots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/continuity/restore/{id}")
async def restore_continuity_snapshot(id: str):
    success = runtime.restore_workspace_snapshot(id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"Snapshot '{id}' not found or failed to restore"
        )
    return {
        "status": "success",
        "message": f"Workspace state successfully restored from snapshot '{id}'",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
