"""SAGE Knowledge Acquisition Layer (SKAL) - deterministic intake boundary."""

import uuid
from typing import Dict, Any, List
from pydantic import BaseModel, Field, model_validator
from sage.models import MemoryObject, ConfidenceLevel


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
            confidence=ConfidenceLevel.VALIDATED,
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
