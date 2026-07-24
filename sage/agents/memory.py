"""SAGE Agent Memory Interface for SAGE Agent Workflow Layer v1."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sage.agents.models import AgentIdentity, AgentTask
from sage.models import MemoryObject, ConfidenceLevel


class AgentMemoryInterface:
    """Provides a connection layer bridging SAGE's core memory stores with governed agents.

    Supports episodic task logging, short-term working memory access, and retrieving
    long-term wisdom from the Master Archive.
    """

    def __init__(self, memory_store, archive_store):
        """Initialize AgentMemoryInterface."""
        self.memory = memory_store
        self.archive = archive_store

    def record_episodic_event(self, agent: AgentIdentity, task: AgentTask, description: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create and store an episodic task event inside SAGE's working memory ledger.

        Args:
            agent: The executing agent's identity.
            task: The governed task context.
            description: Description of step performed.
            metadata: Associated execution metadata.

        Returns:
            The memory ID of the stored episodic record.
        """
        ts = datetime.now(timezone.utc).isoformat()
        content = {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "task_id": task.task_id,
            "objective_id": task.objective_id,
            "description": description,
            "timestamp": ts,
            "metadata": metadata or {},
        }

        memory_obj = MemoryObject(
            object_type="agent_episodic_event",
            content=content,
            tags=["agent_workflow", agent.role.lower(), f"task_{task.task_id}"],
            confidence=ConfidenceLevel.HYPOTHESIS,
        )

        # Store to SAGE's memory store
        if hasattr(self.memory, "store"):
            return self.memory.store(memory_obj)
        else:
            # Fallback if raw dict or dict storage
            ref_id = f"episodic_{datetime.now().timestamp()}"
            self.memory[ref_id] = memory_obj
            return ref_id

    def retrieve_archive_wisdom(self, title_query: str) -> List[Dict[str, Any]]:
        """Query SAGE's Master Archive to retrieve validated structural guidance.

        Args:
            title_query: Text query matching target archive titles.

        Returns:
            List of matching archive entry dictionaries.
        """
        results = []
        if hasattr(self.archive, "search_by_title"):
            entries = self.archive.search_by_title(title_query)
            results = [e.model_dump() for e in entries]
        elif hasattr(self.archive, "list_all"):
            entries = self.archive.list_all()
            for entry in entries:
                if title_query.lower() in entry.title.lower():
                    results.append(entry.model_dump())
        return results
