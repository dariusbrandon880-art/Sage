"""Repository-side Integration Layers for Phase 2 Platform Expansion.

Supports ChatGPT, Google AI (Gemini/Jules), GitHub, Google Workspace,
and Unified Engineering Continuity.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from sage.models import MemoryObject, ConfidenceLevel, DecisionType

# ---------------------------------------------------------------------------
# Pydantic Schemas for Integrations
# ---------------------------------------------------------------------------


class ChatGPTContextRequest(BaseModel):
    query: str


class ChatGPTReasonRequest(BaseModel):
    decision_type: str
    description: str
    rationale: str
    evidence: List[str] = Field(default_factory=list)
    reasoning_trace: List[str] = Field(default_factory=list)


class ChatGPTSyncRequest(BaseModel):
    session_id: str
    chat_context: Dict[str, Any] = Field(default_factory=dict)


class GeminiFeedbackRequest(BaseModel):
    task_id: str
    code_changes: str
    test_output: str
    success: bool


class GitHubCommitRequest(BaseModel):
    commit_hash: str
    author: str
    message: str
    changed_files: List[str] = Field(default_factory=list)


class GitHubPullRequestRequest(BaseModel):
    pr_number: int
    title: str
    author: str
    state: str  # e.g., "opened", "closed", "merged"
    body: str
    merged_at: Optional[str] = None


class GitHubCIRunRequest(BaseModel):
    run_id: str
    workflow_name: str
    status: str  # e.g., "success", "failed"
    failure_log: Optional[str] = None


class WorkspaceDocRequest(BaseModel):
    doc_url: str
    doc_type: str  # e.g., "ADR", "Design Doc", "Research Note"
    title: str
    tags: List[str] = Field(default_factory=list)
    decision_id: Optional[str] = None


# ---------------------------------------------------------------------------
# SAGE Integration Manager Implementation
# ---------------------------------------------------------------------------


class SAGEIntegrationManager:
    """Manages Phase 2 platform integrations, binding them to the SAGE core runtime."""

    def __init__(self, runtime: Any):
        self.runtime = runtime

    # -----------------------------------------------------------------------
    # ChatGPT Integration Layer Logic
    # -----------------------------------------------------------------------

    def chatgpt_get_context(self, query: str) -> Dict[str, Any]:
        """Expose semantic and system context to ChatGPT."""
        # Query memory
        memories = self.runtime.memory.search_by_tag(query)
        # Query archive
        archive_entries = self.runtime.archive.search_by_title(query)

        return {
            "query": query,
            "active_objective": self.runtime.current_state.current_objective,
            "active_task": self.runtime.current_state.active_task,
            "blockers": self.runtime.current_state.blockers,
            "relevant_memories": [m.model_dump() for m in memories[:5]],
            "relevant_archive": [a.model_dump() for a in archive_entries[:5]],
        }

    def chatgpt_validated_lookup(self, query: str) -> Dict[str, Any]:
        """Lookup validated archive entries for architectural accuracy."""
        archive_entries = self.runtime.archive.search_by_title(query)
        # Filter memories that are at least VALIDATED or ARCHIVED
        validated_memories = [
            m.model_dump()
            for m in self.runtime.memory.list_all()
            if (
                m.confidence in (ConfidenceLevel.VALIDATED, ConfidenceLevel.ARCHIVED)
                and any(query.lower() in str(val).lower() for val in m.content.values())
            )
        ]

        return {
            "query": query,
            "archive_results": [a.model_dump() for a in archive_entries],
            "validated_memory_results": validated_memories,
        }

    def chatgpt_record_reasoning(self, req: ChatGPTReasonRequest) -> str:
        """Log decision and persist chain-of-thought trace metadata."""
        decision_id = self.runtime.decisions.record_decision(
            decision_type=DecisionType(req.decision_type),
            description=req.description,
            rationale=req.rationale,
            evidence=req.evidence,
        )

        # Link the reasoning trace to memory
        trace_obj = MemoryObject(
            object_type="reasoning_trace",
            content={
                "decision_id": decision_id,
                "reasoning_trace": req.reasoning_trace,
                "recorded_at": datetime.now().isoformat(),
            },
            tags=["reasoning", "chatgpt"],
            confidence=ConfidenceLevel.VALIDATED,
        )
        self.runtime.memory.store(trace_obj)
        return decision_id

    def chatgpt_sync_context(self, session_id: str, chat_context: Dict[str, Any]) -> bool:
        """Associate ChatGPT conversation context with active SAGE session."""
        sync_obj = MemoryObject(
            object_type="chatgpt_sync",
            content={
                "session_id": session_id,
                "chat_context": chat_context,
                "synced_at": datetime.now().isoformat(),
            },
            tags=[session_id, "chatgpt", "sync"],
            confidence=ConfidenceLevel.VALIDATED,
        )
        self.runtime.memory.store(sync_obj)
        return True

    # -----------------------------------------------------------------------
    # Google AI (Gemini/Jules) Integration Layer Logic
    # -----------------------------------------------------------------------

    def gemini_get_repository_index(self) -> Dict[str, Any]:
        """Provides Jules with codebase directory awareness."""
        modules = [
            "sage/acr",
            "sage/registry",
            "sage/intelligence",
            "sage/automation",
            "sage/interfaces",
            "sage/business",
        ]
        return {
            "project_name": "SAGE-ACR",
            "modules": modules,
            "active_workspace": str(self.runtime.workspace_path),
            "status": "online",
        }

    def gemini_get_developer_context(self) -> Dict[str, Any]:
        """Get highly parsed context for Jules engineering operations."""
        return {
            "objective": self.runtime.current_state.current_objective,
            "task": self.runtime.current_state.active_task,
            "blockers": self.runtime.current_state.blockers,
            "session_depth": self.runtime.acr.get_session_depth(),
            "last_checkpoint": self.runtime.acr.get_state_value("last_checkpoint"),
        }

    def gemini_register_feedback(self, req: GeminiFeedbackRequest) -> Dict[str, Any]:
        """Register task completion status and feedback logs inside SAGE."""
        # Store feedback in memory
        feedback_obj = MemoryObject(
            object_type="engineering_feedback",
            content={
                "task_id": req.task_id,
                "code_changes": req.code_changes,
                "test_output": req.test_output,
                "success": req.success,
            },
            tags=["jules", "feedback"],
            confidence=ConfidenceLevel.VALIDATED if req.success else ConfidenceLevel.HYPOTHESIS,
        )
        feedback_id = self.runtime.memory.store(feedback_obj)

        if not req.success:
            # If failed, raise a blocker automatically
            self.runtime.add_blocker(f"Task '{req.task_id}' failing tests: {req.test_output[:100]}")
        else:
            # If success, clear corresponding blockers
            blocker_prefix = f"Task '{req.task_id}'"
            to_remove = [
                b for b in self.runtime.current_state.blockers if b.startswith(blocker_prefix)
            ]
            for b in to_remove:
                self.runtime.resolve_blocker(b)

        return {"feedback_id": feedback_id, "blockers": self.runtime.current_state.blockers}

    # -----------------------------------------------------------------------
    # GitHub Integration Layer Logic
    # -----------------------------------------------------------------------

    def github_sync_commit(self, req: GitHubCommitRequest) -> str:
        """Indexes commit metrics and references them in the memory store."""
        commit_obj = MemoryObject(
            object_type="github_commit",
            content={
                "commit_hash": req.commit_hash,
                "author": req.author,
                "message": req.message,
                "changed_files": req.changed_files,
                "timestamp": datetime.now().isoformat(),
            },
            tags=["github", "commit"],
            confidence=ConfidenceLevel.VALIDATED,
        )
        memory_id = self.runtime.memory.store(commit_obj)

        # Link commit to active task if mentioned in message
        if (
            self.runtime.current_state.active_task
            and req.message.lower() in self.runtime.current_state.active_task.lower()
        ):
            self.runtime.decisions.record_decision(
                decision_type=DecisionType.ARCHITECTURAL,
                description=f"GitHub commit {req.commit_hash[:7]} merged relevant to current task",
                rationale=req.message,
                evidence=[f"commit:{req.commit_hash}"],
            )
        return memory_id

    def github_sync_pull_request(self, req: GitHubPullRequestRequest) -> Dict[str, Any]:
        """Indexes pull requests and promotes associated memory on merge events."""
        pr_obj = MemoryObject(
            object_type="github_pull_request",
            content={
                "pr_number": req.pr_number,
                "title": req.title,
                "author": req.author,
                "state": req.state,
                "body": req.body,
                "merged_at": req.merged_at,
            },
            tags=["github", "pull_request", req.state],
            confidence=ConfidenceLevel.VALIDATED,
        )
        memory_id = self.runtime.memory.store(pr_obj)

        promoted_archive_id = None
        if req.state == "merged":
            # Search memory for any hypotheses/validated entries with related titles to promote to archive
            related_memories = [
                m
                for m in self.runtime.memory.list_all()
                if m.confidence == ConfidenceLevel.VALIDATED
                and any(t in req.title.lower() for t in m.tags)
            ]

            if related_memories:
                target_mem = related_memories[0]
                # Update status in SAGE validation
                from sage.validation import ValidationSystem

                val_sys = ValidationSystem(self.runtime.memory, self.runtime.archive)
                success, result = val_sys.promote_to_archive(
                    target_mem.id,
                    title=f"Archive via PR #{req.pr_number}: {target_mem.object_type}",
                    tags=["github", f"pr-{req.pr_number}"],
                )
                if success:
                    promoted_archive_id = result

        return {
            "memory_id": memory_id,
            "pr_state": req.state,
            "promoted_archive_id": promoted_archive_id,
        }

    def github_sync_ci_run(self, req: GitHubCIRunRequest) -> Dict[str, Any]:
        """Aligns GitHub actions CI status with the SAGE runtime blockers."""
        ci_obj = MemoryObject(
            object_type="github_ci_run",
            content={
                "run_id": req.run_id,
                "workflow_name": req.workflow_name,
                "status": req.status,
                "timestamp": datetime.now().isoformat(),
            },
            tags=["github", "ci", req.status],
            confidence=ConfidenceLevel.VALIDATED,
        )
        self.runtime.memory.store(ci_obj)

        blocker_msg = (
            f"GitHub Actions CI workflow '{req.workflow_name}' failed (Run ID: {req.run_id})"
        )
        if req.status == "failed":
            self.runtime.add_blocker(blocker_msg)
        else:
            self.runtime.resolve_blocker(blocker_msg)

        return {
            "workflow": req.workflow_name,
            "status": req.status,
            "blockers": self.runtime.current_state.blockers,
        }

    # -----------------------------------------------------------------------
    # Google Workspace Integration Layer Logic
    # -----------------------------------------------------------------------

    def workspace_index_document(self, req: WorkspaceDocRequest) -> str:
        """Register Workspace document reference with provenance in SAGE."""
        doc_obj = MemoryObject(
            object_type="workspace_document_index",
            content={
                "doc_url": req.doc_url,
                "doc_type": req.doc_type,
                "title": req.title,
                "decision_id": req.decision_id,
                "indexed_at": datetime.now().isoformat(),
            },
            tags=["workspace", "document", req.doc_type.lower().replace(" ", "_")] + req.tags,
            confidence=ConfidenceLevel.VALIDATED,
        )
        return self.runtime.memory.store(doc_obj)

    def workspace_query_documents(self, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query and return indexed Google Workspace references."""
        all_docs = self.runtime.memory.search_by_type("workspace_document_index")
        if doc_type:
            return [
                d.model_dump()
                for d in all_docs
                if d.content.get("doc_type", "").lower() == doc_type.lower()
            ]
        return [d.model_dump() for d in all_docs]
