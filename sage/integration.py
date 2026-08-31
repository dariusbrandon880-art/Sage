"""SAGE Integration Layer - AI client interfaces and engineering tool connections."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

class AIQueryRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    include_validated_memory: bool = True
    include_knowledge_state: bool = True
    response_override: str | None = None

class AIQueryResponse(BaseModel):
    response_text: str
    reasoning_history: list[str] = Field(default_factory=list)
    referenced_memories: list[str] = Field(default_factory=list)
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BaseAIClient:
    def __init__(self, client_name: str, runtime: Any):
        self.client_name = client_name
        self.runtime = runtime
        self.reasoning_history: list[str] = []

    def retrieve_context(self, prompt: str) -> dict[str, Any]:
        memories = self.runtime.memory.list_all()
        archives = self.runtime.archive.list_all()
        keywords = [word.lower() for word in prompt.split() if len(word) > 3]
        matched_memories = []
        matched_archives = []
        for m in memories:
            for kw in keywords:
                if kw in m.object_type.lower() or any(kw in tag.lower() for tag in m.tags):
                    matched_memories.append(m)
                    break
        for a in archives:
            for kw in keywords:
                if kw in a.title.lower() or any(kw in tag.lower() for tag in a.tags):
                    matched_archives.append(a)
                    break
        return {"matched_memories": [m.model_dump() for m in matched_memories[:5]], "matched_archives": [a.model_dump() for a in matched_archives[:5]]}

    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        raise NotImplementedError

class ChatGPTClient(BaseAIClient):
    """Connector for OpenAI ChatGPT services behind the canonical SAGE boundary."""
    def __init__(self, runtime: Any, c2_provider: Any = None):
        super().__init__("ChatGPT", runtime)
        self.c2_provider = c2_provider

    def _rehydrate_c2_context(self, session_id: str) -> dict[str, Any]:
        if self.c2_provider and callable(self.c2_provider):
            context = self.c2_provider()
            if context is None:
                raise ValueError("SAGE C2 provider returned no canonical context")
            return dict(context)
        if hasattr(self.runtime, "get_c2_context") and callable(self.runtime.get_c2_context):
            context = self.runtime.get_c2_context(session_id)
            if context is None:
                raise ValueError("SAGE runtime returned no canonical C2 context")
            return dict(context)
        if hasattr(self.runtime, "get_status"):
            status = self.runtime.get_status()
            return {"c2_identity": "ChatGPT", "master_archive_authority": True, "active_objective": status.get("current_objective"), "active_task": status.get("active_task"), "governance_status": "ACTIVE", "c2_status": status.get("c2_status", {}), "active_frontier": "c2-runtime-boundary", "gate": "GOVERNED_EXECUTION"}
        raise ValueError("SAGE runtime cannot rehydrate canonical C2 context")

    def _build_governed_runtime(self, *, session_id: str, c2_context: dict[str, Any], evidence_refs: tuple[str, ...]):
        from hashlib import sha256
        from sage.runtime.model_gateway import SAGERuntime, SAGEStateSnapshot
        objective = c2_context.get("active_objective") or getattr(self.runtime.current_state, "current_objective", None)
        snapshot = SAGEStateSnapshot(
            state_version=str(c2_context.get("state_version") or "runtime-canonical-v1"),
            instance_id=str(c2_context.get("instance_id") or "sage-runtime"),
            mission_id=str(c2_context.get("mission_id") or sha256(str(objective or session_id).encode("utf-8")).hexdigest()),
            session_id=session_id,
            authority_scope=str(c2_context.get("authority_scope") or "director"),
            active_frontier=str(c2_context.get("active_frontier") or "c2-runtime-boundary"),
            stop_boundary=str(c2_context.get("stop_boundary") or "governance"),
            evidence_refs=evidence_refs,
            known_state_refs=tuple(c2_context.get("known_state_refs", ()) or ()),
            candidate_state_refs=tuple(c2_context.get("candidate_state_refs", ()) or ()),
            negative_memory_refs=tuple(c2_context.get("negative_memory_refs", ()) or ()),
        )
        return SAGERuntime(snapshot, policy_version=str(c2_context.get("policy_version") or "sage-runtime-v1"))

    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        context = self.retrieve_context(request.prompt)
        session_id = request.session_id or getattr(getattr(self.runtime, "context", None), "session_id", None) or f"session_{uuid.uuid4().hex[:8]}"
        c2_context = self._rehydrate_c2_context(session_id)
        referenced_ids = tuple([m["id"] for m in context["matched_memories"]] + [a["id"] for a in context["matched_archives"]])
        governed_runtime = self._build_governed_runtime(session_id=session_id, c2_context=c2_context, evidence_refs=referenced_ids)
        if request.response_override:
            class _OverrideResponses:
                def create(self, **kwargs):
                    class _Response:
                        output_text = request.response_override
                    return _Response()
            class _OverrideClient:
                responses = _OverrideResponses()
            provider_client = _OverrideClient()
            self.reasoning_history.append(f"ChatGPT boundary used a governed response override for session '{session_id}'.")
        else:
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            import openai
            provider_client = openai.OpenAI(api_key=api_key)
            self.reasoning_history.append(f"ChatGPT executed through the governed OpenAI adapter for session '{session_id}'.")
        from sage.runtime.chatgpt_sage_boundary import SAGEChatGPTBoundary
        from sage.runtime.model_adapters import OpenAIResponsesAdapter
        from sage.c2.immersion_rehydration import build_chatgpt_immersion_state
        adapter = OpenAIResponsesAdapter(client=provider_client, model_id="gpt-4o-mini")
        immersion_state = build_chatgpt_immersion_state(self.runtime, session_id=session_id, c2_context=c2_context, evidence_refs=referenced_ids)
        rendered_immersion, model_response = SAGEChatGPTBoundary(governed_runtime, adapter).respond(request.prompt, model_role="chatgpt", immersion_state=immersion_state)
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(session_id=session_id, objective=str(c2_context.get("active_objective") or self.runtime.current_state.current_objective or "SAGE Runtime Standby"), task=f"ChatGPT Query: {request.prompt[:50]}...", memories=[{"id": f"ai_chatgpt_{uuid.uuid4().hex[:8]}", "object_type": "ai_query_interaction", "content": {"prompt": request.prompt, "response": model_response.raw_output, "rendered_immersion": rendered_immersion, "referenced_memories": list(referenced_ids), "client": "ChatGPT", "state_digest": model_response.input_state_digest, "station": model_response.station, "policy_version": model_response.policy_version, "provenance_digest": model_response.provenance_digest}, "tags": ["ai_query", "chatgpt", "sage_governed_boundary"], "confidence": "validated"}], decisions=[])
        self.runtime.ingest_session_payload(payload)
        return AIQueryResponse(response_text=rendered_immersion, reasoning_history=self.reasoning_history.copy(), referenced_memories=list(referenced_ids), session_id=session_id)

class GeminiJulesClient(BaseAIClient):
    """Connector for Google Gemini / Jules continuity workflow."""
    def __init__(self, runtime: Any, c2_provider: Any = None):
        super().__init__("GeminiJules", runtime)
        self.c2_provider = c2_provider
    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        context = self.retrieve_context(request.prompt)
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        c2_context = {}
        if self.c2_provider and callable(self.c2_provider): c2_context = dict(self.c2_provider() or {})
        elif hasattr(self.runtime, "get_c2_context") and callable(self.runtime.get_c2_context): c2_context = dict(self.runtime.get_c2_context(session_id) or {})
        elif hasattr(self.runtime, "get_status"):
            status = self.runtime.get_status()
            c2_context = {"c2_identity": "GeminiJules", "master_archive_authority": True, "active_objective": status.get("current_objective"), "active_task": status.get("active_task"), "governance_status": "ACTIVE"}
        referenced_ids = [m["id"] for m in context["matched_memories"]] + [a["id"] for a in context["matched_archives"]]
        self.reasoning_history.append(f"Gemini/Jules rehydrated C2 context for session '{session_id}' and aligned with {len(referenced_ids)} SAGE knowledge artifacts.")
        response_text = request.response_override or (f"[SAGE::C2::GOOGLE] Deep continuation response from Google builder station.\nC2 Operating Context rehydrated successfully: {json.dumps(c2_context, default=str)}\nReferenced SAGE keys: {referenced_ids}")
        from sage.runtime.model_gateway import SAGEProtocolGovernor
        structured = SAGEProtocolGovernor.validate_and_parse(str(response_text), required_station="[SAGE::C2::GOOGLE]")
        if structured.violations: raise RuntimeError(f"SAGE Protocol Governance Violation: {'; '.join(structured.violations)}")
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(session_id=session_id, objective=self.runtime.current_state.current_objective or "AI Query Execution", task=f"GeminiJules Query: {request.prompt[:50]}...", memories=[{"id": f"ai_gemini_{uuid.uuid4().hex[:8]}", "object_type": "ai_query_interaction", "content": {"prompt": request.prompt, "response": response_text, "referenced_memories": referenced_ids, "c2_context": c2_context, "client": "GeminiJules"}, "tags": ["ai_query", "gemini_jules", "c2_rehydrated"], "confidence": "validated"}], decisions=[])
        self.runtime.ingest_session_payload(payload)
        return AIQueryResponse(response_text=response_text, reasoning_history=self.reasoning_history.copy(), referenced_memories=referenced_ids, session_id=session_id)

class GitHubEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"gh_{uuid.uuid4().hex[:8]}")
    event_type: str
    repository: str
    ref: str | None = None
    author: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)

class GoogleWorkspaceArtifact(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    last_modified_by: str
    last_modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class ToolIntegrationManager:
    def __init__(self, runtime: Any):
        self.runtime = runtime
        self.indexed_github_events: list[GitHubEvent] = []
        self.indexed_workspace_artifacts: list[GoogleWorkspaceArtifact] = []
    def index_github_event(self, event: GitHubEvent) -> str:
        self.indexed_github_events.append(event)
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(session_id=f"gh_session_{event.event_id}", objective=self.runtime.current_state.current_objective or f"Index GitHub events for {event.repository}", task=f"Ingest GitHub Event: {event.event_type}", memories=[{"id": event.event_id, "object_type": "github_event", "content": event.model_dump(), "tags": ["github", event.event_type, event.repository], "confidence": "validated"}], decisions=[])
        self.runtime.ingest_session_payload(payload)
        return event.event_id
    def index_workspace_artifact(self, artifact: GoogleWorkspaceArtifact) -> str:
        self.indexed_workspace_artifacts.append(artifact)
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(session_id=f"ws_session_{artifact.doc_id}", objective=self.runtime.current_state.current_objective or "Index Google Workspace documents", task=f"Ingest Google Workspace Document: {artifact.title}", memories=[{"id": artifact.doc_id, "object_type": "workspace_artifact", "content": artifact.model_dump(), "tags": ["google_workspace", artifact.doc_type], "confidence": "validated"}], decisions=[])
        self.runtime.ingest_session_payload(payload)
        return artifact.doc_id
    def get_relationship_index(self, query_tag: str) -> dict[str, Any]:
        matching_gh = [e.model_dump() for e in self.indexed_github_events if query_tag.lower() in e.payload.get("message", "").lower() or query_tag.lower() in e.repository.lower()]
        matching_gw = [a.model_dump() for a in self.indexed_workspace_artifacts if query_tag.lower() in a.title.lower() or query_tag.lower() in a.metadata.get("description", "").lower()]
        return {"query_tag": query_tag, "connected_github_events": matching_gh, "connected_workspace_artifacts": matching_gw}

class GoogleWorkspaceSyncManager:
    SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]
    def __init__(self, runtime: Any): self.runtime = runtime
    def sync_to_google_workspace(self, credentials_path: str | None = None) -> dict[str, Any]:
        docs_to_sync = {"docs/master/MASTER_SNAPSHOT.md": "SAGE Master Snapshot", "docs/master/ROADMAP.md": "SAGE Strategic Roadmap", "docs/master/SESSION_STATE.md": "SAGE Session State", "docs/master/COMMAND_CENTER.md": "SAGE Command Center Manual"}
        synced_docs = []
        for path_str, doc_title in docs_to_sync.items():
            p = Path(path_str); content = p.read_text() if p.exists() else ""
            synced_docs.append({"source_file": path_str, "title": doc_title, "character_count": len(content), "is_empty": not content})
        status = self.runtime.get_status()
        return {"mode": "dry-run", "status": "prepared", "reason": "Missing required Google API packages or credentials file.", "required_scopes": self.SCOPES, "setup_requirements": {"packages_to_install": ["google-api-python-client", "google-auth-oauthlib", "google-auth-httplib2"]}, "sync_mappings": {"google_docs": synced_docs, "google_sheets": {"Engineering Tracker": {"active_task": status.get("active_task"), "current_objective": status.get("current_objective")}}}}

class GoogleDriveProjectionSyncManager:
    CANONICAL_FILES = ["00_MASTER_INDEX.md", "01_GOVERNANCE.md", "02_FAILURE_MEMORY.md", "03_CURRENT_FRONTIER.md", "04_VALIDATED_BASELINE.md", "05_ACTIVE_WORK.md", "06_LATEST_EXECUTION_REPORT.md", "07_NEXT_COMPOUND.md"]
    def __init__(self, runtime: Any = None): self.runtime = runtime
    def calculate_sha256(self, filepath: Path) -> str:
        import hashlib
        return "missing" if not filepath.exists() else hashlib.sha256(filepath.read_bytes()).hexdigest()
    def detect_local_head_sha(self, target_dir_path: Path) -> str:
        active_work_file = target_dir_path / "05_ACTIVE_WORK.md"
        if active_work_file.exists():
            for line in active_work_file.read_text().splitlines():
                if line.startswith("CURRENT_HEAD_SHA:"): return line.split(":", 1)[1].strip()
        import subprocess
        try: return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        except Exception: return "unknown_local_head"
    def sync_projection_to_drive(self, credentials_path: str | None = None, target_dir: str = "SAGE") -> dict[str, Any]:
        target_dir_path = Path(target_dir); local_head = self.detect_local_head_sha(target_dir_path); synced_files = []
        for filename in self.CANONICAL_FILES:
            filepath = target_dir_path / filename; exists = filepath.exists()
            synced_files.append({"filename": filename, "exists_locally": exists, "character_count": len(filepath.read_text()) if exists else 0, "local_sha256": self.calculate_sha256(filepath)})
        google_apis_available = google_auth_available = False
        try:
            import google.oauth2.credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
            google_apis_available = google_auth_available = True
        except ImportError: pass
        cred_path = Path(credentials_path or ".sage/credentials.json")
        if not (google_apis_available and google_auth_available and cred_path.exists()):
            return {"mode": "dry-run", "status": "validation_required", "reason": "Google Workspace packages/credentials unavailable or authentication configuration errors. Live Google Drive verification is blocked.", "required_scopes": ["https://www.googleapis.com/auth/drive.file"], "setup_requirements": {"packages_to_install": ["google-api-python-client", "google-auth-oauthlib", "google-auth-httplib2"], "how_to_install": "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2", "oauth_credentials_json": "A valid 'credentials.json' from Google Cloud Console placed at .sage/credentials.json"}, "stale_conflict_check": {"local_head_sha": local_head, "remote_head_sha": "unknown_dry_run", "status": "VALIDATION_REQUIRED"}, "synced_files": synced_files, "is_valid": False}
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2 import service_account
        try:
            try: creds = service_account.Credentials.from_service_account_file(str(cred_path), scopes=["https://www.googleapis.com/auth/drive.file"])
            except Exception:
                from google_auth_oauthlib.flow import InstalledAppFlow
                creds = InstalledAppFlow.from_client_secrets_file(str(cred_path), scopes=["https://www.googleapis.com/auth/drive.file"]).run_local_server(port=0, open_browser=False)
            service = build("drive", "v3", credentials=creds); files_api = service.files()
            folders = files_api.list(q="name = 'SAGE' and mimeType = 'application/vnd.google-apps.folder' and trashed = false", spaces="drive", fields="files(id, name)").execute().get("files", [])
            folder_id = folders[0]["id"] if folders else files_api.create(body={"name": "SAGE", "mimeType": "application/vnd.google-apps.folder"}, fields="id").execute().get("id")
            live_synced_files = []
            for item in synced_files:
                local_path = target_dir_path / item["filename"]
                if not local_path.exists(): continue
                files = files_api.list(q=f"name = '{item['filename']}' and '{folder_id}' in parents and trashed = false", spaces="drive", fields="files(id, name)").execute().get("files", [])
                media = MediaFileUpload(str(local_path), mimetype="text/markdown", resumable=True)
                if files: file_id = files_api.update(fileId=files[0]["id"], media_body=media, fields="id").execute().get("id"); action = "updated"
                else: file_id = files_api.create(body={"name": item["filename"], "parents": [folder_id]}, media_body=media, fields="id").execute().get("id"); action = "created"
                live_synced_files.append({"filename": item["filename"], "file_id": file_id, "action": action})
            remote_head = "unknown"
            aw_files = files_api.list(q=f"name = '05_ACTIVE_WORK.md' and '{folder_id}' in parents and trashed = false", spaces="drive", fields="files(id)").execute().get("files", [])
            if aw_files:
                remote_content = files_api.get_media(fileId=aw_files[0]["id"]).execute().decode("utf-8", errors="ignore")
                for line in remote_content.splitlines():
                    if line.startswith("CURRENT_HEAD_SHA:"): remote_head = line.split(":", 1)[1].strip(); break
            stale_status = "SYNCHRONIZED" if remote_head in ("unknown", local_head) else "STALE / CONFLICTED PROJECTION"
            return {"mode": "live", "status": "success", "synced_files_count": len(live_synced_files), "synced_files": live_synced_files, "stale_conflict_check": {"local_head_sha": local_head, "remote_head_sha": remote_head, "status": stale_status}, "message": "Synchronized successfully with Google Drive SAGE/ folder.", "is_valid": stale_status == "SYNCHRONIZED"}
        except Exception as e: return {"mode": "live", "status": "failed", "error": str(e), "stale_conflict_check": {"local_head_sha": local_head, "remote_head_sha": "unknown", "status": "ERROR"}, "is_valid": False}
