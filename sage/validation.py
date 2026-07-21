"""Validation system for SAGE memory promotion to Master Archive."""

from typing import Tuple, List, Optional
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
        tags: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Archive a validated memory object by promoting it to the Master Archive.

        Args:
            memory_id: ID of the validated memory object
            title: Title for the archived entry
            tags: Optional tags to merge with original tags

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

        # Construct Archive Entry
        entry_id = f"archive_{obj.id}"
        archive_entry = ArchiveEntry(
            id=entry_id,
            title=title,
            tags=list(set((tags or []) + obj.tags)),
            knowledge_state=KnowledgeState.ARCHIVED,
            content=obj.content,
            lineage=[obj.id]
        )

        try:
            # Promote to Master Archive
            archive_id = self.archive.promote_to_archive(archive_entry)

            # Update memory object's confidence to ARCHIVED
            obj.confidence = ConfidenceLevel.ARCHIVED
            if hasattr(self.memory, "store"):
                self.memory.store(obj)

            return True, archive_id
        except Exception as e:
            return False, f"Failed to promote to archive: {str(e)}"
