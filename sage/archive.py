"""Archive system for permanent, validated knowledge."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

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
        entry.validation_timestamp = datetime.utcnow()
        entry.knowledge_state = KnowledgeState.ARCHIVED
        
        self.entries[entry.id] = entry
        
        # Persist to disk
        filepath = self.storage_path / f"{entry.id}.json"
        with open(filepath, 'w') as f:
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
            with open(filepath, 'r') as f:
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
        return [entry for entry in self.entries.values() 
                if title_substring.lower() in entry.title.lower()]

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
            "validated_at": entry.validation_timestamp.isoformat() if entry.validation_timestamp else None,
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
        return [entry for entry in self.entries.values() 
                if entry.knowledge_state == state]

    def _load_all_entries(self):
        """Load all persisted archive entries from disk."""
        if not self.storage_path.exists():
            return
        
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
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
            "timestamp": datetime.utcnow().isoformat(),
            "entry_count": len(self.entries),
            "entries": [entry.model_dump() for entry in self.entries.values()]
        }
