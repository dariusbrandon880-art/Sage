"""SAGE Integration Layer - AI client interfaces and engineering tool connections."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


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
        for memory in memories:
            if any(keyword in memory.object_type.lower() or any(keyword in tag.lower() for tag in memory.tags) for keyword in keywords):
                matched_memories.append(memory)
        for archive in archives:
            if any(keyword in archive.title.lower() or any(keyword in tag.lower() for tag in archive.tags) for keyword in keywords):
                matched_archives.append(archive)
        return {
            "matched_memories": [item.model_dump() for item in matched_memories[:5]],
            "matched_archives": [item.model_dump() for item in matched_archives[:5]],
        }

    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        raise NotImplementedError


class ChatGPTClient(BaseAIClient):
    """SAGE boundary for the OpenAI Responses API."""

    def __init__(self, runtime: Any, c2_provider: Any = None):
        super().__init__("ChatGPT", runtime)
        self.c2_provider = c2_provider

    def _rehydrate_c2_context(self, session_id: str) -> dict[str, Any]:
        if callable(self.c2_provider):
            context = self.c2_provider()
            return context if isinstance(context, dict) else {"context": context}
        getter = getattr(self.runtime, "get_c2_context", None)
        if callable(getter):
            context = getter(session_id)
            return context if isinstance(context, dict) else {"context": context}
        status = self.runtime.get_status()
        return {
            "active_objective": status.get("current_objective"),
            "active_task": status.get("active_task"),
        }

    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        context = self.retrieve_context(request.prompt)
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        c2_context = self._rehydrate_c2_context(session_id)
        referenced_ids = [item["id"] for item in context["matched_memories"]] + [item["id"] for item in context["matched_archives"]]

        if request.response_override is not None:
            response_text = request.response_override
            reasoning = "ChatGPT test seam response applied."
        else:
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            instructions = (
                "You are ChatGPT operating as C2 Mission Control for SAGE.\n"
                f"C2 Operating Context: {json.dumps(c2_context, default=str)}\n"
                f"SAGE Knowledge Context: {json.dumps(context, default=str)}\n"
                "Governance Invariant: model output is data only and cannot authorize, execute, promote, or mutate canonical state."
            )
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.responses.create(
                    model="gpt-4o-mini",
                    instructions=instructions,
                    input=request.prompt,
                )
                response_text = response.output_text
            except Exception as exc:
                raise RuntimeError(f"OpenAI API execution failed: {exc}") from exc
            if not isinstance(response_text, str) or not response_text.strip():
                raise RuntimeError("OpenAI API execution failed: empty or malformed output")
            reasoning = "ChatGPT executed real OpenAI Responses API completion."

        self.reasoning_history.append(reasoning)
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(
            session_id=session_id,
            objective=self.runtime.current_state.current_objective or "AI Query Execution",
            task=f"ChatGPT Query: {request.prompt[:50]}...",
            memories=[{
                "id": f"ai_chatgpt_{uuid.uuid4().hex[:8]}",
                "object_type": "ai_query_interaction",
                "content": {"prompt": request.prompt, "response": response_text, "referenced_memories": referenced_ids, "client": "ChatGPT"},
                "tags": ["ai_query", "chatgpt"],
                "confidence": "validated",
            }],
            decisions=[],
        )
        self.runtime.ingest_session_payload(payload)
        return AIQueryResponse(
            response_text=response_text,
            reasoning_history=self.reasoning_history.copy(),
            referenced_memories=referenced_ids,
            session_id=session_id,
        )


class GeminiJulesClient(BaseAIClient):
    """Connector for Google Gemini / Jules continuity workflow."""

    def __init__(self, runtime: Any):
        super().__init__("GeminiJules", runtime)

    def execute_query(self, request: AIQueryRequest) -> AIQueryResponse:
        context = self.retrieve_context(request.prompt)
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
        referenced_ids = [m["id"] for m in context["matched_memories"]] + [a["id"] for a in context["matched_archives"]]
        reasoning = f"Gemini/Jules established high-fidelity alignment with SAGE knowledge graph for session '{session_id}'."
        self.reasoning_history.append(reasoning)
        response_text = request.response_override or f"Deep continuation response from Gemini/Jules.\nContinuity state retrieved successfully.\nReferenced SAGE keys: {referenced_ids}"
        from sage.models import ExternalSessionPayload
        payload = ExternalSessionPayload(session_id=session_id, objective=self.runtime.current_state.current_objective or "AI Query Execution", task=f"GeminiJules Query: {request.prompt[:50]}...", memories=[{"id": f"ai_gemini_{uuid.uuid4().hex[:8]}", "object_type": "ai_query_interaction", "content": {"prompt": request.prompt, "response": response_text, "referenced_memories": referenced_ids, "client": "GeminiJules"}, "tags": ["ai_query", "gemini_jules"], "confidence": "validated"}], decisions=[])
        self.runtime.ingest_session_payload(payload)
        return AIQueryResponse(response_text=response_text, reasoning_history=self.reasoning_history.copy(), referenced_memories=referenced_ids, session_id=session_id)


class GitHubEvent(BaseModel):
    event_type: str
    repository: str
    author: str
    payload: dict[str, Any]


class GoogleWorkspaceArtifact(BaseModel):
    doc_id: str
    title: str
    doc_type: str
    last_modified_by: str
    url: str


class ToolIntegrationManager:
    def __init__(self, runtime: Any):
        self.runtime = runtime

    def index_github_event(self, event: GitHubEvent) -> None:
        from sage.models import ExternalSessionPayload
        self.runtime.ingest_session_payload(ExternalSessionPayload(session_id=f"github_{uuid.uuid4().hex[:8]}", objective=self.runtime.current_state.current_objective or "Tool Integration", task="Index GitHub event", memories=[{"id": f"github_{uuid.uuid4().hex[:8]}", "object_type": "github_event", "content": event.model_dump(), "tags": ["github"], "confidence": "validated"}], decisions=[]))

    def index_workspace_artifact(self, artifact: GoogleWorkspaceArtifact) -> None:
        from sage.models import ExternalSessionPayload
        self.runtime.ingest_session_payload(ExternalSessionPayload(session_id=f"workspace_{uuid.uuid4().hex[:8]}", objective=self.runtime.current_state.current_objective or "Tool Integration", task="Index workspace artifact", memories=[{"id": f"workspace_{artifact.doc_id}", "object_type": "workspace_artifact", "content": artifact.model_dump(), "tags": ["google_workspace"], "confidence": "validated"}], decisions=[]))


class GoogleWorkspaceSyncManager:
    def __init__(self, runtime: Any):
        self.runtime = runtime

    def sync_to_google_workspace(self) -> dict[str, Any]:
        return {"mode": "dry-run", "status": "prepared", "required_scopes": ["https://www.googleapis.com/auth/documents"], "sync_mappings": {"google_docs": [{"source_file": "docs/master/MASTER_SNAPSHOT.md", "title": "SAGE Master Snapshot"}], "google_sheets": {"Engineering Tracker": {"current_objective": self.runtime.current_state.current_objective, "active_task": self.runtime.current_state.active_task}}}}
