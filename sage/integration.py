"""SAGE Integration Layer - AI client interfaces and engineering tool connections."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# --- AI Integration Models & Clients ---


class AIQueryRequest(BaseModel):
    """Structure for AI client queries."""

    prompt: str
    session_id: str | None = None
    include_validated_memory: bool = True
    include_knowledge_state: bool = True
    response_override: str | None = None


class AIQueryResponse(BaseModel):
    """Structure for AI client responses."""

    response_text: str
    reasoning_history: list[str] = Field(default_factory=list)
    referenced_memories: list[str] = Field(default_factory=list)
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseAIClient:
    """Base class for AI integration connectors."""

    def __init__(self, client_name: str, runtime: Any):
        self.client_name = client_name
        self.runtime = runtime
        self.reasoning_history: list[str] = []

    def retrieve_context(self, prompt: str) -> dict[str, Any]:
        """Retrieve relevant context and engineering knowledge for the prompt."""
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
        return {
            "matched_memories": [m.model_dump() for m in matched_memories[:5]],
            "matched_archives": [a.model_dump() for a in matched_archives[:5]],
        }

    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        """Process AI query, utilizing context retrieval, memory lookups, and session tracking."""
        raise NotImplementedError


class ChatGPTClient(BaseAIClient):
    """Connector for OpenAI ChatGPT services.

    The response surface is deliberately downstream of the canonical SAGE
    runtime boundary. This class no longer invents immersion state or renders
    directly from model output.
    """

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
            return {
                "c2_identity": "ChatGPT",
                "master_archive_authority": True,
                "active_objective": status.get("current_objective"),
                "active_task": status.get("active_task"),
                "governance_status": "ACTIVE",
                "c2_status": status.get("c2_status", {}),
                "active_frontier": "c2-runtime-boundary",
                "gate": "GOVERNED_EXECUTION",
            }
        raise ValueError("SAGE runtime cannot rehydrate canonical C2 context")

    def _build_governed_runtime(self, *, session_id: str, c2_context: dict[str, Any], evidence_refs: tuple[str, ...]):
        from hashlib import sha256
        from sage.runtime.model_gateway import SAGERuntime, SAGEStateSnapshot

        objective = c2_context.get("active_objective") or getattr(self.runtime.current_state, "current_objective", None)
        if not objective:
            raise ValueError("SAGE ChatGPT boundary requires a canonical active objective")
        task = c2_context.get("active_task") or getattr(self.runtime.current_state, "active_task", None)
        if not task:
            raise ValueError("SAGE ChatGPT boundary requires a canonical active task")
        state_version = str(c2_context.get("state_version") or "runtime-canonical-v1")
        instance_id = str(c2_context.get("instance_id") or "sage-runtime")
        mission_id = str(c2_context.get("mission_id") or sha256(str(objective).encode("utf-8")).hexdigest())
        snapshot = SAGEStateSnapshot(
            state_version=state_version,
            instance_id=instance_id,
            mission_id=mission_id,
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
        session_id = request.session_id or getattr(getattr(self.runtime, "context", None), "session_id", None)
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"

        c2_context = self._rehydrate_c2_context(session_id)
        referenced_ids = tuple(
            [m["id"] for m in context["matched_memories"]]
            + [a["id"] for a in context["matched_archives"]]
        )
        governed_runtime = self._build_governed_runtime(
            session_id=session_id,
            c2_context=c2_context,
            evidence_refs=referenced_ids,
        )

        if request.response_override:
            class _OverrideResponses:
                def create(self, **kwargs):
                    class _Response:
                        output_text = request.response_override
                    return _Response()
            class _OverrideClient:
                responses = _OverrideResponses()
            provider_client = _OverrideClient()
            reasoning = f"ChatGPT boundary used a governed response override for session '{session_id}'."
        else:
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            import openai
            provider_client = openai.OpenAI(api_key=api_key)
            reasoning = f"ChatGPT executed through the governed OpenAI adapter for session '{session_id}'."
        self.reasoning_history.append(reasoning)

        from sage.runtime.chatgpt_sage_boundary import SAGEChatGPTBoundary
        from sage.runtime.model_adapters import OpenAIResponsesAdapter
        from sage.c2.immersion_rehydration import build_chatgpt_immersion_state

        adapter = OpenAIResponsesAdapter(client=provider_client, model_id="gpt-4o-mini")
        immersion_state = build_chatgpt_immersion_state(
            self.runtime,
            session_id=session_id,
            c2_context=c2_context,
            evidence_refs=referenced_ids,
        )
        rendered_immersion, model_response = SAGEChatGPTBoundary(
            governed_runtime,
            adapter,
        ).respond(
            request.prompt,
            model_role="chatgpt",
            immersion_state=immersion_state,
        )

        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(
            session_id=session_id,
            objective=str(c2_context.get("active_objective") or self.runtime.current_state.current_objective),
            task=f"ChatGPT Query: {request.prompt[:50]}...",
            memories=[
                {
                    "id": f"ai_chatgpt_{uuid.uuid4().hex[:8]}",
                    "object_type": "ai_query_interaction",
                    "content": {
                        "prompt": request.prompt,
                        "response": model_response.raw_output,
                        "rendered_immersion": rendered_immersion,
                        "referenced_memories": list(referenced_ids),
                        "client": "ChatGPT",
                        "state_digest": model_response.input_state_digest,
                        "station": model_response.station,
                        "policy_version": model_response.policy_version,
                        "provenance_digest": model_response.provenance_digest,
                    },
                    "tags": ["ai_query", "chatgpt", "sage_governed_boundary"],
                    "confidence": "validated",
                }
            ],
            decisions=[],
        )
        self.runtime.ingest_session_payload(payload)

        return AIQueryResponse(
            response_text=rendered_immersion,
            reasoning_history=self.reasoning_history.copy(),
            referenced_memories=list(referenced_ids),
            session_id=session_id,
        )


class GeminiJulesClient(BaseAIClient):
    """Connector for Google Gemini / Jules continuity workflow."""

    def __init__(self, runtime: Any, c2_provider: Any = None):
        super().__init__("GeminiJules", runtime)
        self.c2_provider = c2_provider

    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        context = self.retrieve_context(request.prompt)
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        c2_context = {}
        if self.c2_provider and callable(self.c2_provider):
            c2_context = dict(self.c2_provider() or {})
        elif hasattr(self.runtime, "get_c2_context") and callable(self.runtime.get_c2_context):
            c2_context = dict(self.runtime.get_c2_context(session_id) or {})
        elif hasattr(self.runtime, "get_status"):
            status = self.runtime.get_status()
            c2_context = {
                "c2_identity": "GeminiJules",
                "master_archive_authority": True,
                "active_objective": status.get("current_objective"),
                "active_task": status.get("active_task"),
                "governance_status": "ACTIVE",
            }
        referenced_ids = [m["id"] for m in context["matched_memories"]] + [a["id"] for a in context["matched_archives"]]
        reasoning = f"Gemini/Jules rehydrated C2 context for session '{session_id}' and aligned with {len(referenced_ids)} SAGE knowledge artifacts."
        self.reasoning_history.append(reasoning)
        response_text = request.response_override or (
            "Deep continuation response from Gemini/Jules station.\n"
            f"C2 Operating Context rehydrated successfully: {json.dumps(c2_context, default=str)}\n"
            f"Referenced SAGE keys: {referenced_ids}"
        )
        from sage.runtime.model_gateway import SAGEProtocolGovernor
        structured = SAGEProtocolGovernor.validate_and_parse(str(response_text), required_station="[SAGE::C2::GEMINI_JULES]")
        if structured.violations:
            raise RuntimeError(f"SAGE Protocol Governance Violation: {'; '.join(structured.violations)}")
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(
            session_id=session_id,
            objective=self.runtime.current_state.current_objective or "AI Query Execution",
            task=f"GeminiJules Query: {request.prompt[:50]}...",
            memories=[{
                "id": f"ai_gemini_{uuid.uuid4().hex[:8]}",
                "object_type": "ai_query_interaction",
                "content": {"prompt": request.prompt, "response": response_text, "referenced_memories": referenced_ids, "c2_context": c2_context, "client": "GeminiJules"},
                "tags": ["ai_query", "gemini_jules", "c2_rehydrated"],
                "confidence": "validated",
            }],
            decisions=[],
        )
        self.runtime.ingest_session_payload(payload)
        return AIQueryResponse(response_text=response_text, reasoning_history=self.reasoning_history.copy(), referenced_memories=referenced_ids, session_id=session_id)


# --- Engineering Tool Integration Models ---


class GitHubEvent(BaseModel):
    """Model for repository-side GitHub webhook/event ingestion."""
    event_id: str = Field(default_factory=lambda: f"gh_{uuid.uuid4().hex[:8]}")
    event_type: str
    repository: str
    ref: str | None = None
    author: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any] = Field(default_factory=dict)


class GoogleWorkspaceArtifact(BaseModel):
    """Model for Google Workspace documentation artifacts."""
    doc_id: str
    title: str
    doc_type: str
    last_modified_by: str
    last_modified_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolIntegrationManager:
    """Manages connections to GitHub and Google Workspace without duplicating source databases."""
    def __init__(self, runtime: Any):
        self.runtime = runtime
        self.indexed_github_events: list[GitHubEvent] = []
        self.indexed_workspace_artifacts: list[GoogleWorkspaceArtifact] = []

    def index_github_event(self, event: GitHubEvent) -> str:
        self.indexed_github_events.append(event)
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(
            session_id=f"gh_session_{event.event_id}",
            objective=self.runtime.current_state.current_objective or f"Index GitHub events for {event.repository}",
            task=f"Ingest GitHub Event: {event.event_type}",
            memories=[{"id": event.event_id, "object_type": "github_event", "content": event.model_dump(), "tags": ["github", event.event_type, event.repository], "confidence": "validated"}],
            decisions=[],
        )
        self.runtime.ingest_session_payload(payload)
        return event.event_id

    def index_workspace_artifact(self, artifact: GoogleWorkspaceArtifact) -> str:
        self.indexed_workspace_artifacts.append(artifact)
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(
            session_id=f"ws_session_{artifact.doc_id}",
            objective=self.runtime.current_state.current_objective or "Index Google Workspace documents",
            task=f"Ingest Google Workspace Document: {artifact.title}",
            memories=[{"id": artifact.doc_id, "object_type": "workspace_artifact", "content": artifact.model_dump(), "tags": ["google_workspace", artifact.doc_type], "confidence": "validated"}],
            decisions=[],
        )
        self.runtime.ingest_session_payload(payload)
        return artifact.doc_id

    def get_relationship_index(self, query_tag: str) -> dict[str, Any]:
        matching_gh = [e.model_dump() for e in self.indexed_github_events if query_tag.lower() in e.payload.get("message", "").lower() or query_tag.lower() in e.repository.lower()]
        matching_gw = [a.model_dump() for a in self.indexed_workspace_artifacts if query_tag.lower() in a.title.lower() or query_tag.lower() in a.metadata.get("description", "").lower()]
        return {"query_tag": query_tag, "connected_github_events": matching_gh, "connected_workspace_artifacts": matching_gw}
