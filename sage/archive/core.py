"""Archive system for permanent, validated knowledge."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sage.models import ArchiveEntry, KnowledgeState


class Archive:
    """Master Archive - source of truth for validated knowledge."""

    def __init__(self, storage_path: str = "sage_data/archive"):
        """Initialize archive.

        Args:
            storage_path: Path to store archive entries
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.entries: Dict[str, ArchiveEntry] = {}
        self._load_all_entries()

    def promote_to_archive(self, entry: ArchiveEntry) -> str:
        """Promote validated knowledge to Master Archive.

        Args:
            entry: ArchiveEntry to promote

        Returns:
            ID of archived entry
        """
        entry.validation_timestamp = datetime.now(timezone.utc)
        entry.knowledge_state = KnowledgeState.ARCHIVED

        self.entries[entry.id] = entry

        # Persist to disk
        filepath = self.storage_path / f"{entry.id}.json"
        with open(filepath, "w") as f:
            json.dump(entry.model_dump(), f, indent=2, default=str)

        return entry.id

    def retrieve_entry(self, entry_id: str) -> Optional[ArchiveEntry]:
        """Retrieve an archive entry.

        Args:
            entry_id: ID of entry to retrieve

        Returns:
            ArchiveEntry if found, None otherwise
        """
        if entry_id in self.entries:
            return self.entries[entry_id]

        # Try loading from disk
        filepath = self.storage_path / f"{entry_id}.json"
        if filepath.exists():
            with open(filepath, "r") as f:
                data = json.load(f)
                entry = ArchiveEntry(**data)
                self.entries[entry_id] = entry
                return entry

        return None

    def search_by_tag(self, tag: str) -> List[ArchiveEntry]:
        """Search archive entries by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of matching ArchiveEntries
        """
        results = []
        for entry in self.entries.values():
            if tag in entry.tags:
                results.append(entry)
        return results

    def search_by_title(self, title_substring: str) -> List[ArchiveEntry]:
        """Search archive entries by title substring.

        Args:
            title_substring: Substring to search for in title

        Returns:
            List of matching ArchiveEntries
        """
        return [
            entry
            for entry in self.entries.values()
            if title_substring.lower() in entry.title.lower()
        ]

    def get_lineage(self, entry_id: str) -> Dict[str, Any]:
        """Get full lineage of an archive entry.

        Args:
            entry_id: ID of archive entry

        Returns:
            Lineage information
        """
        entry = self.retrieve_entry(entry_id)
        if not entry:
            return {}

        return {
            "entry_id": entry_id,
            "title": entry.title,
            "decision_history": entry.decision_history,
            "memory_lineage": entry.lineage,
            "created_at": entry.created_at.isoformat(),
            "validated_at": (
                entry.validation_timestamp.isoformat() if entry.validation_timestamp else None
            ),
        }

    def list_all(self) -> List[ArchiveEntry]:
        """List all archive entries.

        Returns:
            List of all ArchiveEntries
        """
        return list(self.entries.values())

    def get_by_state(self, state: KnowledgeState) -> List[ArchiveEntry]:
        """Get archive entries by knowledge state.

        Args:
            state: Knowledge state to filter by

        Returns:
            List of ArchiveEntries with matching state
        """
        return [entry for entry in self.entries.values() if entry.knowledge_state == state]

    def _load_all_entries(self):
        """Load all persisted archive entries from disk."""
        if not self.storage_path.exists():
            return

        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    entry = ArchiveEntry(**data)
                    self.entries[entry.id] = entry
            except Exception as e:
                print(f"Error loading archive entry from {filepath}: {e}")

    def export_state(self) -> Dict[str, Any]:
        """Export current archive state.

        Returns:
            Dictionary representation of all archive entries
        """
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry_count": len(self.entries),
            "entries": [entry.model_dump() for entry in self.entries.values()],
        }

    def get_knowledge_graph(self):
        """Retrieve the compiled knowledge graph of all archive entries and relationships."""
        from sage.archive.knowledge_graph import KnowledgeGraph
        from sage.archive.relationships import KnowledgeRelationship

        graph = KnowledgeGraph()
        for entry in self.entries.values():
            graph.add_node(entry.id)
            if entry.intelligence:
                # Add individual relationships
                for rel in entry.intelligence.relationships:
                    graph.add_relationship(rel)
                # Add relationships for decisions
                for dec in entry.intelligence.decisions:
                    graph.add_relationship(
                        KnowledgeRelationship(
                            source_id=entry.id,
                            target_id=f"decision_{dec.decision_id}",
                            relationship_type="depends_on",
                            metadata={
                                "affected_components": dec.affected_components,
                                "validation_outcome": dec.validation_outcome,
                            },
                        )
                    )
        return graph

    def set_entry_lineage(
        self,
        entry_id: str,
        source: str,
        validation_rules: Optional[List[str]] = None,
        dependent_decisions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set or update lineage details for an archive entry."""
        entry = self.retrieve_entry(entry_id)
        if not entry:
            raise ValueError(f"Archive entry {entry_id} not found.")

        from sage.archive.intelligence import ArchiveIntelligence
        from sage.archive.lineage import KnowledgeLineage, ValidationRecord

        if not entry.intelligence:
            entry.intelligence = ArchiveIntelligence()

        val_record = None
        if validation_rules is not None:
            val_record = ValidationRecord(
                rules_applied=validation_rules,
                validated_by="ValidationSystem",
                timestamp=datetime.now(timezone.utc),
                success=True,
            )

        entry.intelligence.lineage = KnowledgeLineage(
            source=source,
            created_at=entry.created_at,
            validation_record=val_record,
            dependent_decisions=dependent_decisions or [],
            metadata=metadata or {},
        )

        # Re-persist
        self.promote_to_archive(entry)

    def add_entry_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a relationship connection between archive entries."""
        entry = self.retrieve_entry(source_id)
        if not entry:
            raise ValueError(f"Source entry {source_id} not found.")

        from sage.archive.intelligence import ArchiveIntelligence
        from sage.archive.relationships import KnowledgeRelationship

        if not entry.intelligence:
            entry.intelligence = ArchiveIntelligence()

        rel = KnowledgeRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            metadata=metadata or {},
        )

        # Check if already exists to prevent duplicate addition
        exists = any(
            r.source_id == rel.source_id
            and r.target_id == rel.target_id
            and r.relationship_type == rel.relationship_type
            for r in entry.intelligence.relationships
        )
        if not exists:
            entry.intelligence.relationships.append(rel)

        # Re-persist
        self.promote_to_archive(entry)

        # Also add inverse relationship to target entry if it exists to keep graph fully bidirectional
        target_entry = self.retrieve_entry(target_id)
        if target_entry:
            if not target_entry.intelligence:
                target_entry.intelligence = ArchiveIntelligence()

            target_rel = KnowledgeRelationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=relationship_type,
                metadata=metadata or {},
            )
            exists_target = any(
                r.source_id == target_rel.source_id
                and r.target_id == target_rel.target_id
                and r.relationship_type == target_rel.relationship_type
                for r in target_entry.intelligence.relationships
            )
            if not exists_target:
                target_entry.intelligence.relationships.append(target_rel)
                self.promote_to_archive(target_entry)

    def set_entry_confidence(
        self,
        entry_id: str,
        confidence_level: float,
        validation_status: str = "archived",
        evidence_references: Optional[List[str]] = None,
        review_notes: Optional[str] = None,
        reviewer: str = "system",
    ) -> None:
        """Explicitly assign/update confidence level, validation status, and review history."""
        entry = self.retrieve_entry(entry_id)
        if not entry:
            raise ValueError(f"Archive entry {entry_id} not found.")

        from sage.archive.intelligence import ArchiveIntelligence
        from sage.archive.confidence import ConfidenceTracker, ReviewHistoryItem

        if not entry.intelligence:
            entry.intelligence = ArchiveIntelligence()

        if not entry.intelligence.confidence:
            entry.intelligence.confidence = ConfidenceTracker(
                confidence_level=confidence_level,
                validation_status=validation_status,
                evidence_references=evidence_references or [],
            )
        else:
            entry.intelligence.confidence.confidence_level = confidence_level
            entry.intelligence.confidence.validation_status = validation_status
            if evidence_references is not None:
                entry.intelligence.confidence.evidence_references = evidence_references

        # Add a review history item
        entry.intelligence.confidence.review_history.append(
            ReviewHistoryItem(
                reviewer=reviewer,
                timestamp=datetime.now(timezone.utc),
                status=validation_status,
                notes=review_notes,
            )
        )

        # Re-persist
        self.promote_to_archive(entry)

    def add_entry_decision(
        self,
        entry_id: str,
        decision_id: str,
        affected_components: Optional[List[str]] = None,
        reasoning_reference: Optional[str] = None,
        validation_outcome: Optional[str] = None,
        successor_decisions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Connect an architecture decision to an archive entry."""
        entry = self.retrieve_entry(entry_id)
        if not entry:
            raise ValueError(f"Archive entry {entry_id} not found.")

        from sage.archive.intelligence import ArchiveIntelligence
        from sage.archive.relationships import DecisionConnection

        if not entry.intelligence:
            entry.intelligence = ArchiveIntelligence()

        conn = DecisionConnection(
            decision_id=decision_id,
            affected_components=affected_components or [],
            reasoning_reference=reasoning_reference,
            validation_outcome=validation_outcome,
            successor_decisions=successor_decisions or [],
            metadata=metadata or {},
        )

        # Prevent duplicates
        exists = any(d.decision_id == decision_id for d in entry.intelligence.decisions)
        if not exists:
            entry.intelligence.decisions.append(conn)

        # Add decision to decision_history list if not present
        if decision_id not in entry.decision_history:
            entry.decision_history.append(decision_id)

        # Re-persist
        self.promote_to_archive(entry)
