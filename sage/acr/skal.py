"""SAGE Knowledge Acquisition Layer (SKAL) - deterministic intake boundary."""

import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, model_validator
from sage.models import MemoryObject, ConfidenceLevel, ArchiveEntry, KnowledgeState


class SKALValidationReport(BaseModel):
    """Structured Pydantic schema for validation reports supporting snake_case and spaced keys."""

    report_name: str = Field(validation_alias="report_name")
    status: str
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            normalized = {}
            for k, v in data.items():
                norm_key = k.replace(" ", "_").lower()
                normalized[norm_key] = v
            # Map report_name aliases
            if "report_name" not in normalized and "report name" in data:
                normalized["report_name"] = data["report name"]
            return normalized
        return data


class SKALDeploymentEvent(BaseModel):
    """Structured Pydantic schema for deployment events supporting snake_case and spaced keys."""

    event_name: str = Field(validation_alias="event_name")
    environment: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            normalized = {}
            for k, v in data.items():
                norm_key = k.replace(" ", "_").lower()
                normalized[norm_key] = v
            if "event_name" not in normalized and "event name" in data:
                normalized["event_name"] = data["event name"]
            return normalized
        return data


class SKALArchitectureDecision(BaseModel):
    """Structured Pydantic schema for architecture decisions supporting snake_case and spaced keys."""

    decision_id: str = Field(validation_alias="decision_id")
    title: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            normalized = {}
            for k, v in data.items():
                norm_key = k.replace(" ", "_").lower()
                normalized[norm_key] = v
            if "decision_id" not in normalized and "decision id" in data:
                normalized["decision_id"] = data["decision id"]
            return normalized
        return data


class SKALIntakeManager:
    """Manages SKAL deterministic intake process, validates external payloads, and routes them."""

    def __init__(self, memory_store, runtime_engine=None):
        self.memory = memory_store
        self.runtime = runtime_engine

    def process_incoming_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validates incoming payload, preserves evidence lineage, and routes to active session.

        Args:
            payload: Dict representing the incoming intake record

        Returns:
            Dict containing processing status, validation details, and generated record ID.
        """
        # Determine payload type
        normalized_payload = {}
        for k, v in payload.items():
            normalized_payload[k.replace(" ", "_").lower()] = v

        payload_type = normalized_payload.get("payload_type") or normalized_payload.get("type")
        if not payload_type:
            # Infer from fields
            if "report_name" in normalized_payload or "report name" in payload:
                payload_type = "validation_report"
            elif "event_name" in normalized_payload or "event name" in payload:
                payload_type = "deployment_event"
            elif "decision_id" in normalized_payload or "decision id" in payload:
                payload_type = "architecture_decision"
            else:
                return {
                    "success": False,
                    "error": "Could not determine SKAL payload type. Please provide 'payload_type' or matching schema keys.",
                }

        data_content = normalized_payload.get("data") or payload

        validated_model = None
        errors = []

        try:
            if payload_type == "validation_report":
                validated_model = SKALValidationReport(**data_content)
            elif payload_type == "deployment_event":
                validated_model = SKALDeploymentEvent(**data_content)
            elif payload_type == "architecture_decision":
                validated_model = SKALArchitectureDecision(**data_content)
            else:
                return {"success": False, "error": f"Unknown SKAL payload type: '{payload_type}'"}
        except Exception as e:
            errors.append(str(e))
            return {
                "success": False,
                "error": "Validation failed",
                "details": errors,
                "payload_type": payload_type,
            }

        # Create MemoryObject to preserve evidence lineage
        memory_id = f"skal_intake_{uuid.uuid4().hex[:8]}"
        memory_obj = MemoryObject(
            id=memory_id,
            object_type=f"skal_{payload_type}",
            content=validated_model.model_dump(),
            tags=["skal", payload_type],
            confidence=ConfidenceLevel.HYPOTHESIS,  # Stays at Hypothesis until validated & promoted!
        )

        self.memory.store(memory_obj)

        # Route to active session if available
        session_id = None
        if self.runtime and self.runtime.context and self.runtime.context.session_id:
            session_id = self.runtime.context.session_id
            session_state = self.runtime.session_manager.retrieve_session(session_id)
            if session_state:
                session_state.add_completed_action(f"skal_intake:{payload_type}:{memory_id}")
                self.runtime.session_manager.save_session(session_state)

        return {
            "success": True,
            "payload_type": payload_type,
            "memory_id": memory_id,
            "session_id": session_id,
            "data": validated_model.model_dump(),
        }

    def promote_skal_record(
        self, memory_id: str, authorizer_signature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enforces SAGE-RT-KL-002 Governed Knowledge Promotion Contract on SKAL records.

        Rules:
        - Research / Candidates cannot bypass Validation.
        - Master Archive promotion requires explicit validation authority (authorizer_signature).
        - Architecture decisions must preserve lineage to source evidence.
        - Deployment events update operational state only, bypassing Master Archive.

        Args:
            memory_id: ID of the SKAL memory record to promote.
            authorizer_signature: Digital/human approval signature key.

        Returns:
            Dict representing status and results of the promotion operation.
        """
        stored_obj = self.memory.retrieve(memory_id)
        if not stored_obj:
            return {"success": False, "error": f"Memory record '{memory_id}' not found."}

        if not stored_obj.object_type.startswith("skal_"):
            return {"success": False, "error": f"Record '{memory_id}' is not a valid SKAL record."}

        payload_type = stored_obj.object_type.replace("skal_", "")

        # 1. Validation Authority check: Signature is required for Master Archive promotion
        if payload_type in ["validation_report", "architecture_decision"]:
            if not authorizer_signature or authorizer_signature.strip() == "":
                return {
                    "success": False,
                    "error": "SAGE-RT-KL-002 Violation: Authorized signature is required for Master Archive promotion.",
                }

        # 2. Schema specific routing logic
        if payload_type == "validation_report":
            status = stored_obj.content.get("status")
            if status != "passed":
                return {
                    "success": False,
                    "error": f"Promotion rejected: Validation report status is '{status}' (must be 'passed').",
                }

            # Validated & Promote
            stored_obj.confidence = ConfidenceLevel.VALIDATED
            self.memory.store(stored_obj)

            # Move to Master Archive
            archive_entry_id = f"archive_skal_{stored_obj.id}"
            archive_entry = ArchiveEntry(
                id=archive_entry_id,
                title=stored_obj.content.get("report_name") or "SKAL Validation Report",
                tags=["skal", "validation", "promoted"],
                knowledge_state=KnowledgeState.ARCHIVED,
                lineage=[stored_obj.id],
                content=stored_obj.content,
            )
            if self.runtime and self.runtime.archive:
                self.runtime.archive.promote_to_archive(archive_entry)

            return {
                "success": True,
                "status": "promoted",
                "archive_id": archive_entry_id,
                "message": "Validation report promoted successfully to Master Archive.",
            }

        elif payload_type == "architecture_decision":
            # Must preserve lineage (evidence must be declared in metadata/evidence)
            metadata = stored_obj.content.get("metadata") or {}
            evidence = metadata.get("evidence") or []
            if not evidence:
                return {
                    "success": False,
                    "error": "SAGE-RT-KL-002 Violation: Architecture decisions must preserve lineage to source evidence.",
                }

            stored_obj.confidence = ConfidenceLevel.VALIDATED
            self.memory.store(stored_obj)

            # Record via DecisionTracker if runtime is available
            if self.runtime and self.runtime.decisions:
                from sage.models import DecisionType

                self.runtime.decisions.record_decision(
                    decision_type=DecisionType.ARCHITECTURAL,
                    description=stored_obj.content.get("description", ""),
                    rationale=stored_obj.content.get("title", ""),
                    evidence=evidence,
                )

            # Move to Master Archive
            archive_entry_id = f"archive_skal_{stored_obj.id}"
            archive_entry = ArchiveEntry(
                id=archive_entry_id,
                title=stored_obj.content.get("title") or "SKAL Architecture Decision",
                tags=["skal", "architecture", "promoted"],
                knowledge_state=KnowledgeState.ARCHIVED,
                lineage=[stored_obj.id] + list(evidence),
                content=stored_obj.content,
            )
            if self.runtime and self.runtime.archive:
                self.runtime.archive.promote_to_archive(archive_entry)

            return {
                "success": True,
                "status": "promoted",
                "archive_id": archive_entry_id,
                "message": "Architecture decision recorded and promoted successfully to Master Archive.",
            }

        elif payload_type == "deployment_event":
            # Deployment events update operational state only, bypassing Master Archive
            stored_obj.confidence = ConfidenceLevel.VALIDATED
            self.memory.store(stored_obj)

            # Update active runtime session if available
            session_id = None
            if self.runtime and self.runtime.context and self.runtime.context.session_id:
                session_id = self.runtime.context.session_id
                session_state = self.runtime.session_manager.retrieve_session(session_id)
                if session_state:
                    session_state.metadata["last_deployment_event"] = stored_obj.content
                    session_state.metadata["deployment_status"] = stored_obj.content.get("status")
                    self.runtime.session_manager.save_session(session_state)

            return {
                "success": True,
                "status": "operational_updated",
                "session_id": session_id,
                "message": "Deployment event processed. Operational state updated. Master Archive bypassed.",
            }

        return {"success": False, "error": f"Unhandled SKAL record type '{payload_type}'."}
