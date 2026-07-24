"""SAGE-SKAL (Semantic Knowledge Association Layer) deterministic intake boundary.

This module implements the deterministic intake gateway that validates external information
before promotion into SAGE knowledge systems, preserving evidence lineage.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, BaseModel, Field, ValidationError

from sage.models import ArchiveEntry, ConfidenceLevel, DecisionType, KnowledgeState, MemoryObject


class ValidationReport(BaseModel):
    """Schema for a validation report payload."""

    source: str
    timestamp: datetime | str
    commit_identifier: str = Field(
        validation_alias=AliasChoices("commit_identifier", "commit identifier")
    )
    validation_results: dict[str, Any] = Field(
        validation_alias=AliasChoices("validation_results", "validation results")
    )
    evidence_references: list[str] = Field(
        validation_alias=AliasChoices("evidence_references", "evidence references")
    )
    confidence_metadata: dict[str, Any] = Field(
        validation_alias=AliasChoices("confidence_metadata", "confidence metadata")
    )

    model_config = {
        "populate_by_name": True,
    }


class DeploymentEvent(BaseModel):
    """Schema for a deployment event payload."""

    source: str
    deployment_target: str = Field(
        validation_alias=AliasChoices("deployment_target", "deployment target")
    )
    status: str
    commit_identifier: str = Field(
        validation_alias=AliasChoices("commit_identifier", "commit identifier")
    )
    log_payload: dict[str, Any] = Field(validation_alias=AliasChoices("log_payload", "log payload"))

    model_config = {
        "populate_by_name": True,
    }


class ArchitectureDecision(BaseModel):
    """Schema for an architecture decision payload."""

    proposal: str
    reasoning: str
    validation_requirements: list[str] = Field(
        validation_alias=AliasChoices("validation_requirements", "validation requirements")
    )
    approval_state: str = Field(validation_alias=AliasChoices("approval_state", "approval state"))

    model_config = {
        "populate_by_name": True,
    }


def process_incoming_payload(
    payload_type: str,
    payload_data: dict[str, Any],
    runtime: Any,
) -> dict[str, Any]:
    """SAGE-SKAL deterministic intake gateway.

    Accepts structured input, validates schemas supporting both snake_case and spaced keys,
    rejects malformed data, and preserves evidence lineage in temporary memory store (without
    directly modifying permanent knowledge storage).
    """
    valid_types = ["validation_report", "deployment_event", "architecture_decision"]
    if payload_type not in valid_types:
        raise ValueError(
            f"Unsupported SAGE-SKAL payload type: '{payload_type}'. Must be one of {valid_types}."
        )

    # Validate schema
    try:
        if payload_type == "validation_report":
            validated_model = ValidationReport(**payload_data)
        elif payload_type == "deployment_event":
            validated_model = DeploymentEvent(**payload_data)
        elif payload_type == "architecture_decision":
            validated_model = ArchitectureDecision(**payload_data)
        else:
            raise ValueError(f"Unmapped payload type: {payload_type}")
    except (ValidationError, ValueError) as e:
        raise ValueError(f"SAGE-SKAL schema validation failed for {payload_type}: {e!s}")

    memory_id = f"skal_{payload_type}_{uuid.uuid4().hex[:8]}"

    # Setup tags for searching/tracking
    tags = ["skal", payload_type]

    # Dynamically extract source identifier for tagging
    if hasattr(validated_model, "source"):
        tags.append(validated_model.source)
    elif hasattr(validated_model, "proposal"):
        # Use first few words or a hash for proposal tag if too long
        proposal_tag = validated_model.proposal[:20].replace(" ", "_").lower()
        tags.append(proposal_tag)

    if hasattr(validated_model, "commit_identifier") and validated_model.commit_identifier:
        tags.append(validated_model.commit_identifier)

    # Construct the memory object
    memory_obj = MemoryObject(
        id=memory_id,
        object_type=f"skal_{payload_type}",
        content=validated_model.model_dump(mode="json"),
        tags=tags,
        confidence=ConfidenceLevel.HYPOTHESIS,
    )

    # Store memory object in SAGE's temporary memory store
    runtime.memory.store(memory_obj)

    # Route to active runtime session if context exists
    if runtime.context and runtime.context.session_id:
        session_state = runtime.session_manager.retrieve_session(runtime.context.session_id)
        if session_state:
            session_state.add_completed_action(f"skal_intake:{payload_type}:{memory_id}")
            runtime.session_manager.save_session(session_state)

        runtime.context_tracker.add_recent_change(
            f"SAGE-SKAL Ingested validated {payload_type} evidence lineage: {memory_id}"
        )

    return {
        "status": "success",
        "message": f"Successfully validated and ingested SAGE-SKAL {payload_type}.",
        "payload_type": payload_type,
        "memory_id": memory_id,
        "data": validated_model.model_dump(mode="json"),
    }


def _append_to_markdown_lab(
    file_path: str, memory_id: str, payload_type: str, title: str, details: str
) -> None:
    """Helper to append an operational lineage entry to a markdown file on disk."""
    path = Path(file_path)
    if not path.exists():
        return

    log_entry = (
        f"\n### SAGE-SKAL Promoted Lineage Entry: {memory_id}\n"
        f"- **Timestamp**: {datetime.now(timezone.utc).isoformat()}\n"
        f"- **Payload Type**: `{payload_type}`\n"
        f"- **Title/Subject**: {title}\n"
        f"- **Lineage Details**: {details}\n"
    )

    try:
        with open(path, "a") as f:
            f.write(log_entry)
    except OSError:
        pass


def promote_skal_payload(
    memory_id: str,
    approved: bool,
    approver: str,
    runtime: Any,
    is_research: bool = False,
) -> dict[str, Any]:
    """SAGE-RT-KL-002 Governed Knowledge Promotion Contract execution.

    Connects SAGE-SKAL intake boundary to SAGE governance, routing validated evidence to:
    - Research Lab (docs/labs/RESEARCH_LAB.md)
    - Engineering Lab (docs/labs/ENGINEERING_LAB.md)
    - Validation Lab (docs/labs/VALIDATION_LAB.md)
    - Command Center (docs/master/COMMAND_CENTER.md)
    - Master Archive (docs/master/MASTER_ARCHIVE.md & runtime.archive)
    """
    # 1. Retrieve raw MemoryObject from temporary memory store
    memory_obj = runtime.memory.retrieve(memory_id)
    if not memory_obj:
        raise ValueError(f"SAGE-SKAL memory object '{memory_id}' not found.")

    # 2. Verify it is indeed a SAGE-SKAL payload
    if not memory_obj.object_type.startswith("skal_"):
        raise ValueError(f"Memory object '{memory_id}' is not a valid SAGE-SKAL intake payload.")

    payload_type = memory_obj.object_type.replace("skal_", "")

    # 3. Rule check: Research items cannot directly enter Master Archive
    if is_research:
        if approved:
            raise ValueError("Research items cannot directly enter Master Archive.")

        # Route to Research Lab
        title = (
            memory_obj.content.get("source")
            or memory_obj.content.get("proposal")
            or "Research Item"
        )
        details = f"Unapproved/draft item categorized as research. Processed by {approver}."

        _append_to_markdown_lab(
            "docs/labs/RESEARCH_LAB.md",
            memory_id=memory_id,
            payload_type=payload_type,
            title=title,
            details=details,
        )

        return {
            "status": "success",
            "destination": "Research Lab",
            "memory_id": memory_id,
            "message": f"Research payload '{memory_id}' successfully routed to Research Lab.",
            "is_research": True,
        }

    # 4. Route based on payload types
    if payload_type == "validation_report":
        if approved:
            # Route to Master Archive
            archive_id = f"archive_{memory_id}"
            title = f"Validated Report: {memory_obj.content.get('source', 'unknown')}"

            # Promote to Archive
            from sage.archive.confidence import ConfidenceTracker, ReviewHistoryItem
            from sage.archive.intelligence import ArchiveIntelligence
            from sage.archive.lineage import KnowledgeLineage, ValidationRecord

            val_rec = ValidationRecord(
                validated_by="ValidationSystem",
                timestamp=datetime.now(timezone.utc),
                rules_applied=["SAGE-RT-KL-002", "schema_validation"],
                success=True,
            )

            lineage_record = KnowledgeLineage(
                source=memory_obj.content.get("source") or "skal_intake",
                created_at=memory_obj.created_at,
                validation_record=val_rec,
                dependent_decisions=[],
                metadata={"original_memory_id": memory_id, "approver": approver},
            )

            conf_tracker = ConfidenceTracker(
                confidence_level=1.0,
                validation_status="archived",
                evidence_references=[memory_id],
                review_history=[
                    ReviewHistoryItem(
                        reviewer=approver,
                        timestamp=datetime.now(timezone.utc),
                        status="archived",
                        notes=f"SAGE-SKAL Promotion with authorized signature by {approver}",
                    )
                ],
            )

            archive_entry = ArchiveEntry(
                id=archive_id,
                title=title,
                tags=memory_obj.tags + ["promoted"],
                knowledge_state=KnowledgeState.ARCHIVED,
                content=memory_obj.content,
                lineage=[memory_id],
                intelligence=ArchiveIntelligence(
                    lineage=lineage_record,
                    confidence=conf_tracker,
                    relationships=[],
                    decisions=[],
                ),
            )

            runtime.archive.promote_to_archive(archive_entry)

            # Update memory object's confidence
            memory_obj.confidence = ConfidenceLevel.ARCHIVED
            runtime.memory.store(memory_obj)

            _append_to_markdown_lab(
                "docs/master/MASTER_ARCHIVE.md",
                memory_id=memory_id,
                payload_type=payload_type,
                title=title,
                details=f"Validation report promoted to Master Archive by {approver}.",
            )

            return {
                "status": "success",
                "destination": "Master Archive",
                "memory_id": memory_id,
                "archive_id": archive_id,
                "message": f"ValidationReport '{memory_id}' promoted to Master Archive.",
            }
        else:
            # Route to Validation Lab
            title = f"Draft Report: {memory_obj.content.get('source', 'unknown')}"
            _append_to_markdown_lab(
                "docs/labs/VALIDATION_LAB.md",
                memory_id=memory_id,
                payload_type=payload_type,
                title=title,
                details="Unapproved validation report routed to Validation Lab.",
            )

            return {
                "status": "success",
                "destination": "Validation Lab",
                "memory_id": memory_id,
                "message": f"Unapproved ValidationReport '{memory_id}' routed to Validation Lab.",
            }

    elif payload_type == "architecture_decision":
        if approved:
            # Route to Master Archive (while preserving decision lineage)
            archive_id = f"archive_{memory_id}"
            title = f"Approved Decision: {memory_obj.content.get('proposal', 'unknown')}"

            # Record decision in technical decision tracker
            dec_id = runtime.decisions.record_decision(
                decision_type=DecisionType.ARCHITECTURAL,
                description=memory_obj.content.get("proposal", ""),
                rationale=memory_obj.content.get("reasoning", ""),
                evidence=[memory_id],
            )

            # Promote to Archive
            from sage.archive.confidence import ConfidenceTracker, ReviewHistoryItem
            from sage.archive.intelligence import ArchiveIntelligence
            from sage.archive.lineage import KnowledgeLineage, ValidationRecord
            from sage.archive.relationships import DecisionConnection

            val_rec = ValidationRecord(
                validated_by="ValidationSystem",
                timestamp=datetime.now(timezone.utc),
                rules_applied=["SAGE-RT-KL-002", "schema_validation"],
                success=True,
            )

            lineage_record = KnowledgeLineage(
                source="skal_intake",
                created_at=memory_obj.created_at,
                validation_record=val_rec,
                dependent_decisions=[dec_id],
                metadata={"original_memory_id": memory_id, "approver": approver},
            )

            conf_tracker = ConfidenceTracker(
                confidence_level=1.0,
                validation_status="archived",
                evidence_references=[memory_id],
                review_history=[
                    ReviewHistoryItem(
                        reviewer=approver,
                        timestamp=datetime.now(timezone.utc),
                        status="archived",
                        notes=f"SAGE-SKAL Decision Approved by {approver}",
                    )
                ],
            )

            dec_conn = DecisionConnection(
                decision_id=dec_id,
                affected_components=["SAGE-SKAL Pipeline"],
                reasoning_reference=memory_obj.content.get("reasoning"),
                validation_outcome="Approved & Promoted",
            )

            archive_entry = ArchiveEntry(
                id=archive_id,
                title=title,
                tags=memory_obj.tags + ["promoted", "decision"],
                knowledge_state=KnowledgeState.ARCHIVED,
                content=memory_obj.content,
                lineage=[memory_id],
                decision_history=[dec_id],
                intelligence=ArchiveIntelligence(
                    lineage=lineage_record,
                    confidence=conf_tracker,
                    relationships=[],
                    decisions=[dec_conn],
                ),
            )

            runtime.archive.promote_to_archive(archive_entry)

            # Update memory object's confidence
            memory_obj.confidence = ConfidenceLevel.ARCHIVED
            runtime.memory.store(memory_obj)

            _append_to_markdown_lab(
                "docs/master/MASTER_ARCHIVE.md",
                memory_id=memory_id,
                payload_type=payload_type,
                title=title,
                details=f"Architecture decision '{dec_id}' promoted to Master Archive by {approver}.",
            )

            return {
                "status": "success",
                "destination": "Master Archive",
                "memory_id": memory_id,
                "archive_id": archive_id,
                "decision_id": dec_id,
                "message": f"ArchitectureDecision '{memory_id}' promoted to Master Archive.",
            }
        else:
            # Route to Engineering Lab
            title = f"Draft Decision: {memory_obj.content.get('proposal', 'unknown')}"
            _append_to_markdown_lab(
                "docs/labs/ENGINEERING_LAB.md",
                memory_id=memory_id,
                payload_type=payload_type,
                title=title,
                details="Unapproved decision routed to Engineering Lab.",
            )

            return {
                "status": "success",
                "destination": "Engineering Lab",
                "memory_id": memory_id,
                "message": f"Unapproved ArchitectureDecision '{memory_id}' routed to Engineering Lab.",
            }

    elif payload_type == "deployment_event":
        # Enforce: "Deployment events update operational state only."
        # They cannot enter the Master Archive.
        if approved:
            # Even if approved=True is passed, deployment events only update operational state
            pass

        # Update runtime active task/operational state
        target = memory_obj.content.get("deployment_target") or "unknown"
        status = memory_obj.content.get("status") or "unknown"
        runtime.current_state.active_task = f"Deploy Target: {target} [{status}]"
        runtime._save_state()

        title = f"Deployment to {target} ({status})"
        _append_to_markdown_lab(
            "docs/master/COMMAND_CENTER.md",
            memory_id=memory_id,
            payload_type=payload_type,
            title=title,
            details=f"Deployment event parsed. Operational state updated by {approver}.",
        )

        return {
            "status": "success",
            "destination": "Command Center",
            "memory_id": memory_id,
            "message": f"DeploymentEvent '{memory_id}' updated operational state in Command Center.",
        }

    raise ValueError(f"Unrecognized payload type '{payload_type}' during promotion.")
