"""Validation system for SAGE memory promotion to Master Archive."""

from typing import Tuple, List, Optional, Any
from sage.models import MemoryObject, ConfidenceLevel, ArchiveEntry, KnowledgeState


class ValidationSystem:
    """Validates memory objects and manages their promotion workflow to the Master Archive."""

    def __init__(self, memory_store, archive_store):
        """Initialize validation system.

        Args:
            memory_store: Store managing memory objects (Memory)
            archive_store: Master Archive store (Archive)
        """
        self.memory = memory_store
        self.archive = archive_store

    def validate_memory(self, memory_id: str) -> Tuple[bool, List[str]]:
        """Validate a memory object against standard quality/completeness rules.

        Args:
            memory_id: ID of the memory object to validate

        Returns:
            Tuple of (is_valid, list_of_failed_rule_descriptions)
        """
        # If we have a retrieve method (e.g. from Memory)
        if hasattr(self.memory, "retrieve"):
            obj = self.memory.retrieve(memory_id)
        # Fallback if it's a MemoryStore but might have retrieving capabilities
        elif hasattr(self.memory, "get_memory_entry"):
            obj = self.memory.get_memory_entry("default", memory_id)
        else:
            obj = None

        if not obj:
            return False, ["Memory object not found"]

        # If the obj is a dict or other raw representation, parse it or handle it
        if isinstance(obj, dict):
            obj = MemoryObject(**obj)

        failed_rules = []

        # Rule 1: Content must not be empty
        if not obj.content:
            failed_rules.append("Memory content is empty")

        # Rule 2: Object type must be specified
        if not obj.object_type:
            failed_rules.append("Object type is not specified")

        # Rule 3: Content must have some substance (non-empty keys/values)
        if isinstance(obj.content, dict):
            has_substance = any(str(v).strip() for v in obj.content.values() if v is not None)
            if not has_substance:
                failed_rules.append("Memory content lacks substance")

        is_valid = len(failed_rules) == 0
        return is_valid, failed_rules

    def promote_to_validated(self, memory_id: str) -> Tuple[bool, str]:
        """Promote a memory object's confidence level to VALIDATED if it passes validation.

        Args:
            memory_id: ID of the memory object to promote

        Returns:
            Tuple of (success, message/error)
        """
        if hasattr(self.memory, "retrieve"):
            obj = self.memory.retrieve(memory_id)
        else:
            obj = None

        if not obj:
            return False, "Memory object not found"

        is_valid, failed_rules = self.validate_memory(memory_id)
        if not is_valid:
            return False, f"Validation failed: {', '.join(failed_rules)}"

        obj.confidence = ConfidenceLevel.VALIDATED

        if hasattr(self.memory, "store"):
            self.memory.store(obj)

        return True, "Memory object successfully promoted to VALIDATED"

    def promote_to_archive(
        self,
        memory_id: str,
        title: str,
        tags: Optional[List[str]] = None,
        session_state: Optional[Any] = None,
    ) -> Tuple[bool, str]:
        """Archive a validated memory object by promoting it to the Master Archive.

        Args:
            memory_id: ID of the validated memory object
            title: Title for the archived entry
            tags: Optional tags to merge with original tags
            session_state: Optional SessionState to update with archive reference

        Returns:
            Tuple of (success, archive_entry_id or error_message)
        """
        if hasattr(self.memory, "retrieve"):
            obj = self.memory.retrieve(memory_id)
        else:
            obj = None

        if not obj:
            return False, "Memory object not found"

        # Check if already validated, otherwise validate and promote
        if obj.confidence != ConfidenceLevel.VALIDATED:
            success, msg = self.promote_to_validated(memory_id)
            if not success:
                return False, f"Cannot archive: {msg}"
            # Reload object with new confidence level
            if hasattr(self.memory, "retrieve"):
                obj = self.memory.retrieve(memory_id)

        # Construct Archive Entry with ArchiveIntelligence
        from sage.archive.intelligence import ArchiveIntelligence
        from sage.archive.lineage import KnowledgeLineage, ValidationRecord
        from sage.archive.confidence import ConfidenceTracker, ReviewHistoryItem
        import datetime
        from datetime import timezone

        # Automatic generation of lineage & validation record
        val_rec = ValidationRecord(
            validated_by="ValidationSystem",
            timestamp=datetime.datetime.now(timezone.utc),
            rules_applied=["non_empty_content", "object_type_specified", "content_substance"],
            success=True,
        )

        lineage_record = KnowledgeLineage(
            source=obj.content.get("source") or "memory_store",
            created_at=obj.created_at,
            validation_record=val_rec,
            dependent_decisions=obj.content.get("decisions") or [],
            metadata={"original_memory_id": obj.id, "object_type": obj.object_type},
        )

        # Confidence state
        confidence_level_val = 1.0 if obj.confidence == ConfidenceLevel.VALIDATED else 0.5
        conf_tracker = ConfidenceTracker(
            confidence_level=confidence_level_val,
            validation_status="validated",
            evidence_references=[obj.id],
            review_history=[
                ReviewHistoryItem(
                    reviewer="ValidationSystem",
                    timestamp=datetime.datetime.now(timezone.utc),
                    status="validated",
                    notes="Promoted through SAGE Autonomous Continuity Bridge validation loop",
                )
            ],
        )

        intelligence_bundle = ArchiveIntelligence(
            lineage=lineage_record,
            confidence=conf_tracker,
            relationships=[],
            decisions=[],
        )

        entry_id = f"archive_{obj.id}"
        archive_entry = ArchiveEntry(
            id=entry_id,
            title=title,
            tags=list(set((tags or []) + obj.tags)),
            knowledge_state=KnowledgeState.ARCHIVED,
            content=obj.content,
            lineage=[obj.id],
            intelligence=intelligence_bundle,
        )

        try:
            # Promote to Master Archive
            archive_id = self.archive.promote_to_archive(archive_entry)

            # Update memory object's confidence to ARCHIVED
            obj.confidence = ConfidenceLevel.ARCHIVED
            if hasattr(self.memory, "store"):
                self.memory.store(obj)

            # If session state is provided, link the reference
            if session_state is not None and hasattr(session_state, "add_archive_reference"):
                session_state.add_archive_reference(archive_id)

            return True, archive_id
        except Exception as e:
            return False, f"Failed to promote to archive: {str(e)}"


class ReliabilityIncidentTracker:
    """Manages recording, updating, and querying of structured reliability incidents

    utilizing SAGE's canonical MemoryObjects to prevent database duplication.
    """

    def __init__(self, memory_store):
        """Initialize tracker with canonical Memory backend."""
        self.memory = memory_store

    def record_incident(self, incident: Any) -> str:
        """Convert and store a ReliabilityIncident as a standard SAGE MemoryObject."""
        from sage.models import MemoryObject, ConfidenceLevel

        # If incident is a dict, parse it
        if isinstance(incident, dict):
            from sage.models import ReliabilityIncident

            incident = ReliabilityIncident(**incident)

        obj = MemoryObject(
            id=incident.id,
            object_type="reliability_incident",
            content=incident.model_dump(),
            tags=["reliability", incident.incident_type.value, incident.source],
            confidence=ConfidenceLevel.VALIDATED,
        )
        self.memory.store(obj)
        return incident.id

    def retrieve_incident(self, incident_id: str) -> Optional[Any]:
        """Retrieve a registered reliability incident from memory."""
        from sage.models import ReliabilityIncident

        obj = self.memory.retrieve(incident_id)
        if not obj or obj.object_type != "reliability_incident":
            return None
        return ReliabilityIncident(**obj.content)

    def list_incidents(self) -> List[Any]:
        """List all tracked reliability incidents."""
        from sage.models import ReliabilityIncident

        incidents = []
        for obj in self.memory.list_all():
            if obj.object_type == "reliability_incident":
                try:
                    incidents.append(ReliabilityIncident(**obj.content))
                except Exception:
                    pass
        return incidents

    def resolve_incident(
        self, incident_id: str, status: str, validation_evidence: List[str] = None
    ) -> bool:
        """Update resolution status and validation evidence of an incident."""
        incident = self.retrieve_incident(incident_id)
        if not incident:
            return False

        incident.status = status
        if validation_evidence:
            incident.validation_evidence = list(
                set(incident.validation_evidence + validation_evidence)
            )

        # Resave in memory
        self.record_incident(incident)
        return True
