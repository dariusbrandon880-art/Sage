"""Validation system for SAGE memory objects and knowledge promotion."""

from typing import Tuple, List, Optional
from datetime import datetime
from sage.models import ConfidenceLevel, KnowledgeState, ArchiveEntry, MemoryObject


class ValidationSystem:
    """Validation system for verifying memory objects and promoting them to validated knowledge or the archive."""

    def __init__(self, memory_store, archive):
        """Initialize validation system.

        Args:
            memory_store: Instance of MemoryStore.
            archive: Instance of Archive.
        """
        self.memory = memory_store
        self.archive = archive

    def validate_memory(self, memory_id: str) -> Tuple[bool, List[str]]:
        """Validate a memory object against standard quality/completeness rules.

        Args:
            memory_id: The ID of the memory object to validate.

        Returns:
            A tuple of (is_valid, failed_rules).
        """
        memory_obj = self.memory.retrieve(memory_id)
        if not memory_obj:
            return False, ["Memory object not found"]

        failed_rules = []

        # Rule 1: Non-empty object type
        if not memory_obj.object_type or not memory_obj.object_type.strip():
            failed_rules.append("Object type must not be empty")

        # Rule 2: Non-empty content
        if not memory_obj.content:
            failed_rules.append("Content must not be empty")

        # Rule 3: Must have at least one tag for categorization
        if not memory_obj.tags:
            failed_rules.append("Memory object must have at least one tag")

        # Rule 4: Must have a valid confidence level
        if not isinstance(memory_obj.confidence, ConfidenceLevel):
            failed_rules.append("Invalid confidence level")

        is_valid = len(failed_rules) == 0
        return is_valid, failed_rules

    def promote_to_validated(self, memory_id: str) -> Tuple[bool, str]:
        """Promote a memory object to VALIDATED state if it passes validation.

        Args:
            memory_id: The ID of the memory object to promote.

        Returns:
            A tuple of (success, message).
        """
        memory_obj = self.memory.retrieve(memory_id)
        if not memory_obj:
            return False, "Memory object not found"

        is_valid, failed_rules = self.validate_memory(memory_id)
        if not is_valid:
            return False, f"Validation failed: {', '.join(failed_rules)}"

        memory_obj.confidence = ConfidenceLevel.VALIDATED
        memory_obj.updated_at = datetime.utcnow()
        self.memory.store(memory_obj)

        return True, "Memory object successfully promoted to VALIDATED"

    def promote_to_archive(
        self,
        memory_id: str,
        title: str,
        tags: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Promote validated memory object to the Master Archive as permanent knowledge.

        Args:
            memory_id: The ID of the memory object to promote.
            title: Title of the archive entry.
            tags: Optional tags to merge or override.

        Returns:
            A tuple of (success, archive_id or error_message).
        """
        memory_obj = self.memory.retrieve(memory_id)
        if not memory_obj:
            return False, "Memory object not found"

        # Check if the memory object has been validated first
        if memory_obj.confidence != ConfidenceLevel.VALIDATED:
            return False, "Memory object must be validated before it can be promoted to the archive"

        merged_tags = list(set(memory_obj.tags + (tags or [])))

        # Create ArchiveEntry
        archive_entry = ArchiveEntry(
            title=title,
            content=memory_obj.content,
            tags=merged_tags,
            created_at=memory_obj.created_at,
            validation_timestamp=datetime.utcnow(),
            knowledge_state=KnowledgeState.ARCHIVED,
            decision_history=[],
            lineage={"memory_object_id": memory_obj.id, "object_type": memory_obj.object_type}
        )

        # Promote to master archive
        archive_id = self.archive.promote_to_archive(archive_entry)

        # Update memory object state to ARCHIVED
        memory_obj.confidence = ConfidenceLevel.ARCHIVED
        memory_obj.updated_at = datetime.utcnow()
        self.memory.store(memory_obj)

        return True, archive_id
