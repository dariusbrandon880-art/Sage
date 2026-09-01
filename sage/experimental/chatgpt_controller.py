"""Sage-Governed ChatGPT Controller
 
Manages ChatGPT rendering through Sage governance layers with:
- Context binding to Sage runtime
- Evidence capture for all ChatGPT interactions
- Decision lineage integration
- Validated knowledge lineage enforcement
- Fail-closed authentication gates
"""

import json
import os
from datetime import datetime
from typing import Any, Optional

from openai import OpenAI

from sage.models import MemoryObject, ConfidenceLevel
from sage.evidence_closure import EvidenceClosure


class SageChatGPTController:
    """
    Sage-controlled ChatGPT rendering layer.
    
    All ChatGPT interactions are:
    1. Validated against current Sage governance state
    2. Bound to session context
    3. Logged with full provenance
    4. Stored in evidence layer for decision lineage
    5. Subject to fail-closed authentication
    """
    
    def __init__(self, runtime, api_key: Optional[str] = None):
        """
        Initialize the ChatGPT controller within Sage runtime context.
        
        Args:
            runtime: SAGERuntime instance for governance and memory binding
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.runtime = runtime
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured in environment or constructor")
        
        self.client = OpenAI(api_key=self.api_key)
        self.evidence_closure = EvidenceClosure()
        
    def render_with_governance(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_context: Optional[str] = None,
        bind_to_decision: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Render ChatGPT response through Sage governance layer.
        
        Args:
            prompt: User prompt/query
            model: OpenAI model to use (default: gpt-4)
            max_tokens: Maximum response tokens
            temperature: Temperature for generation (0-2)
            system_context: Optional system prompt for governance
            bind_to_decision: Optional decision ID to bind response to
            
        Returns:
            dict with response, metadata, and evidence reference
            
        Raises:
            RuntimeError: If Sage governance checks fail
            ValueError: If authentication/authorization fails
        """
        # 1. SAGE GOVERNANCE VALIDATION
        session_id = self.runtime.context.session_id if self.runtime.context else None
        if not session_id:
            raise ValueError("No active Sage session - ChatGPT rendering requires session context")
        
        # 2. BUILD GOVERNED SYSTEM CONTEXT
        sage_system = self._build_governed_system_prompt(system_context)
        
        # 3. CAPTURE REQUEST EVIDENCE
        request_evidence = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "model": model,
            "prompt": prompt,
            "system_context_length": len(sage_system),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "decision_binding": bind_to_decision,
        }
        
        # 4. CALL OPENAI WITH GOVERNANCE CONTEXT
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sage_system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95,
            )
            
            # Extract response content
            assistant_message = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
        except Exception as e:
            # FAIL-CLOSED: Log failure and raise
            self._capture_evidence(
                "chatgpt_render_failed",
                {
                    **request_evidence,
                    "error": str(e),
                    "status": "failed",
                },
                session_id
            )
            raise RuntimeError(f"ChatGPT rendering failed: {e}")
        
        # 5. CAPTURE RESPONSE EVIDENCE
        response_evidence = {
            **request_evidence,
            "response": assistant_message,
            "finish_reason": finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "status": "success",
            "timestamp_response": datetime.now().isoformat(),
        }
        
        # 6. STORE EVIDENCE IN SAGE ARCHIVE
        evidence_id = self._capture_evidence(
            "chatgpt_render_success",
            response_evidence,
            session_id
        )
        
        # 7. BIND TO DECISION LINEAGE IF REQUESTED
        if bind_to_decision:
            decision = self.runtime.decisions.retrieve_decision(bind_to_decision)
            if decision:
                decision.evidence.append(evidence_id)
                # Update decision with ChatGPT binding
        
        # 8. RETURN GOVERNED RESPONSE
        return {
            "content": assistant_message,
            "model": model,
            "finish_reason": finish_reason,
            "usage": response_evidence["usage"],
            "evidence_id": evidence_id,
            "session_id": session_id,
            "timestamp": request_evidence["timestamp"],
            "governed": True,
        }
    
    def render_streaming(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_context: Optional[str] = None,
    ):
        """
        Stream ChatGPT response through Sage governance.
        
        Yields chunks of response with governance metadata.
        """
        session_id = self.runtime.context.session_id if self.runtime.context else None
        if not session_id:
            raise ValueError("No active Sage session for streaming render")
        
        sage_system = self._build_governed_system_prompt(system_context)
        
        # Capture streaming start
        stream_start = datetime.now().isoformat()
        
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sage_system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            
            accumulated_content = ""
            chunk_count = 0
            
            for chunk in stream:
                chunk_count += 1
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    accumulated_content += content
                    
                    yield {
                        "chunk": content,
                        "chunk_count": chunk_count,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                    }
            
            # Capture streaming completion
            self._capture_evidence(
                "chatgpt_stream_complete",
                {
                    "session_id": session_id,
                    "model": model,
                    "stream_start": stream_start,
                    "stream_end": datetime.now().isoformat(),
                    "total_chunks": chunk_count,
                    "accumulated_length": len(accumulated_content),
                    "status": "success",
                },
                session_id
            )
            
        except Exception as e:
            self._capture_evidence(
                "chatgpt_stream_failed",
                {
                    "session_id": session_id,
                    "error": str(e),
                    "stream_start": stream_start,
                    "stream_end": datetime.now().isoformat(),
                    "status": "failed",
                },
                session_id
            )
            raise RuntimeError(f"ChatGPT streaming failed: {e}")
    
    def retrieve_context(self, query: str) -> dict[str, Any]:
        """
        Retrieve Sage-governed context for ChatGPT prompt.
        
        Searches memory and archive for relevant context.
        """
        session_id = self.runtime.context.session_id if self.runtime.context else None
        
        # Search Sage memory for relevant context
        memory_results = self.runtime.memory.search_by_tag("chatgpt_context")
        archive_results = self.runtime.archive.search_by_title(query)
        
        return {
            "query": query,
            "session_id": session_id,
            "memory_context": [obj.model_dump() for obj in memory_results],
            "archive_context": [entry.model_dump() for entry in archive_results],
            "timestamp": datetime.now().isoformat(),
        }
    
    def _build_governed_system_prompt(self, custom_system: Optional[str] = None) -> str:
        """
        Build system prompt with Sage governance directives.
        """
        base_system = """You are an AI assistant operating within SAGE (Autonomous Continuity Runtime).

Governance directives:
1. All responses are logged with full provenance for decision lineage
2. Claims must be grounded in provided context or marked as hypothetical
3. Decisions influence SAGE's knowledge evolution and archive
4. Fail-closed authentication: refuse requests without proper session context
5. Evidence preservation: maintain attribution chains for all assertions

Operational mode: GOVERNED by SAGE runtime - all output is subject to validation and evidence capture."""
        
        if custom_system:
            return f"{base_system}\n\n{custom_system}"
        
        return base_system
    
    def _capture_evidence(
        self,
        event_type: str,
        event_data: dict[str, Any],
        session_id: str,
    ) -> str:
        """
        Capture ChatGPT interaction evidence in Sage archive.
        """
        evidence_obj = MemoryObject(
            object_type="chatgpt_interaction",
            content={
                "event_type": event_type,
                "event_data": event_data,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            },
            tags=["chatgpt", "ai_interaction", "evidence", event_type],
            confidence=ConfidenceLevel.VALIDATED,
        )
        
        evidence_id = self.runtime.memory.store(evidence_obj)
        return evidence_id
