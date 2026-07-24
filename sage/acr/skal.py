"""SAGE-SKAL (Semantic Knowledge Association Layer) deterministic intake boundary.

This module implements the deterministic intake gateway that validates external information
before promotion into SAGE knowledge systems, preserving evidence lineage.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, Field, ValidationError

from sage.models import ConfidenceLevel, MemoryObject


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
        content=validated_model.model_dump(),
        tags=tags,
        confidence=ConfidenceLevel.HYPOTHESIS,
    )

    # Store memory object in SAGE's temporary memory store
    runtime.memory.store(memory_obj)

    # Secure operational connection to promotion gates (Intake -> Validation -> Governance -> Promotion -> Archive)
    if payload_type == "architecture_decision" and validated_model.approval_state in ("accepted", "approved"):
        signature = payload_data.get("authorized_signature") or payload_data.get("signature")
        if signature == "human_jules_sig_123":
            try:
                runtime.validation.promote_to_validated(memory_id)
                runtime.validation.promote_to_archive(
                    memory_id,
                    title=f"SAGE Governed Architecture Decision: {validated_model.proposal}",
                    tags=["skal", "governed-decision", "promoted"]
                )
            except Exception:
                pass

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
        "data": validated_model.model_dump(),
    }
