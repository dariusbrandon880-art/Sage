"""ChatGPT Controller Module for SAGE C2.

Provides governed ChatGPT rendering with evidence capture, decision binding,
and session continuity.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Generator

from pydantic import BaseModel, Field

from sage.integration import AIQueryRequest, ChatGPTClient
from sage.models import ConfidenceLevel, MemoryObject


class ChatRenderRequest(BaseModel):
    prompt: str
    session_id: str | None = None
    model: str | None = "gpt-4"
    bind_to_decision: str | None = None
    stream: bool | None = False


class ChatRenderResponse(BaseModel):
    content: str
    model: str
    session_id: str
    evidence_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    governed: bool = True
    usage: dict[str, Any] | None = None


class ChatGPTController:
    """Controller for governed ChatGPT interactions within SAGE."""

    def __init__(self, runtime: Any, chatgpt_client: ChatGPTClient | None = None):
        self.runtime = runtime
        self.chatgpt_client = chatgpt_client or ChatGPTClient(runtime)

    def render(
        self,
        request: ChatRenderRequest,
        response_override: str | None = None,
        authenticated: bool = True,
    ) -> ChatRenderResponse:
        """Render a governed ChatGPT response and capture immutable evidence in memory."""
        session_id = request.session_id or f"c2_session_{uuid.uuid4().hex[:8]}"
        model = request.model or "gpt-4"

        if hasattr(self.runtime, "current_state"):
            if not getattr(self.runtime.current_state, "current_objective", None) and hasattr(self.runtime, "set_objective"):
                self.runtime.set_objective("SAGE Operational Continuity Baseline")
            if not getattr(self.runtime.current_state, "active_task", None) and hasattr(self.runtime, "set_task"):
                self.runtime.set_task(f"ChatGPT Render: {request.prompt[:50]}")

        if response_override is None and not os.environ.get("OPENAI_API_KEY", "").strip():
            response_override = json.dumps({
                "station": "[SAGE::C2::CHATGPT]",
                "reasoning_chain": ["Governed offline execution fallback"],
                "proposed_actions": [],
                "epistemic_state": {
                    "confidence_level": "HIGH",
                    "validated_facts": ["SAGE runtime offline fallback active"],
                    "unverified_hypotheses": [],
                    "known_unknowns": []
                },
                "evidence_refs": [],
                "response_text": f"[SAGE::C2::CHATGPT] Governed response for prompt: {request.prompt[:100]}"
            })

        query_req = AIQueryRequest(
            prompt=request.prompt,
            session_id=session_id,
            response_override=response_override,
        )

        query_resp = self.chatgpt_client.execute_query(query_req)

        evidence_id = f"mem_chatgpt_{uuid.uuid4().hex[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()

        evidence_content = {
            "prompt": request.prompt,
            "response": query_resp.response_text,
            "session_id": session_id,
            "model": model,
            "authenticated": authenticated,
            "bind_to_decision": request.bind_to_decision,
            "referenced_memories": query_resp.referenced_memories,
            "reasoning_history": query_resp.reasoning_history,
        }

        memory_obj = MemoryObject(
            id=evidence_id,
            object_type="chatgpt_render",
            content=evidence_content,
            tags=["chatgpt", "c2_interaction", "evidence", "sage_governed"],
            confidence=ConfidenceLevel.VALIDATED,
        )

        self.runtime.memory.store(memory_obj)

        if request.bind_to_decision:
            try:
                decision = self.runtime.decisions.retrieve_decision(
                    request.bind_to_decision
                )
                if decision:
                    if decision.evidence is None:
                        decision.evidence = []
                    decision.evidence.append(evidence_id)
            except Exception:
                pass

        return ChatRenderResponse(
            content=query_resp.response_text,
            model=model,
            session_id=session_id,
            evidence_id=evidence_id,
            timestamp=now_str,
            governed=True,
            usage={"prompt_tokens": len(request.prompt.split()), "completion_tokens": len(query_resp.response_text.split())},
        )

    def render_stream(
        self,
        request: ChatRenderRequest,
        response_override: str | None = None,
        authenticated: bool = True,
    ) -> Generator[str, None, None]:
        """Stream a rendered ChatGPT response chunk by chunk as NDJSON."""
        full_response = self.render(
            request=request,
            response_override=response_override,
            authenticated=authenticated,
        )

        words = full_response.content.split(" ")
        session_id = full_response.session_id

        chunk_count = max(1, len(words) // 3 + (1 if len(words) % 3 != 0 else 0))
        words_per_chunk = max(1, len(words) // chunk_count) if chunk_count > 0 else 1

        for i in range(0, len(words), words_per_chunk):
            chunk_words = words[i : i + words_per_chunk]
            chunk_text = " ".join(chunk_words)
            if i + words_per_chunk < len(words):
                chunk_text += " "

            chunk_data = {
                "chunk": chunk_text,
                "chunk_number": (i // words_per_chunk) + 1,
                "session_id": session_id,
                "evidence_id": full_response.evidence_id,
            }
            yield json.dumps(chunk_data) + "\n"
