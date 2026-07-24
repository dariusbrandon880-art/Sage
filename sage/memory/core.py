"""Core Memory system for SAGE memory objects."""

import json
from pathlib import Path

from sage.models import MemoryObject


class Memory:
    """Memory database for managing MemoryObject persistence, indexing, and retrieval."""

    def __init__(self, storage_path: str = "sage_data/memory"):
        """Initialize memory storage.

        Args:
            storage_path: Path to store memory objects on disk
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.objects: dict[str, MemoryObject] = {}
        self._load_all()

    def store(self, obj: MemoryObject) -> str:
        """Store/update a memory object and persist to disk.

        Args:
            obj: MemoryObject instance

        Returns:
            The memory object ID
        """
        self.objects[obj.id] = obj
        self._save(obj)
        return obj.id

    def retrieve(self, memory_id: str) -> MemoryObject | None:
        """Retrieve a memory object by ID.

        Args:
            memory_id: ID of the memory object

        Returns:
            MemoryObject if found, None otherwise
        """
        if memory_id in self.objects:
            return self.objects[memory_id]

        filepath = self.storage_path / f"{memory_id}.json"
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    obj = MemoryObject(**data)
                    self.objects[memory_id] = obj
                    return obj
            except Exception:
                pass
        return None

    def list_all(self) -> list[MemoryObject]:
        """List all stored memory objects.

        Returns:
            List of MemoryObjects
        """
        return list(self.objects.values())

    def search_by_tag(self, tag: str) -> list[MemoryObject]:
        """Search memory objects by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of matching MemoryObjects
        """
        return [obj for obj in self.objects.values() if tag in obj.tags]

    def search_by_type(self, object_type: str) -> list[MemoryObject]:
        """Search memory objects by type.

        Args:
            object_type: Object type to filter by

        Returns:
            List of matching MemoryObjects
        """
        return [obj for obj in self.objects.values() if obj.object_type == object_type]

    def _save(self, obj: MemoryObject):
        """Persist a memory object to disk as JSON."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        filepath = self.storage_path / f"{obj.id}.json"
        with open(filepath, "w") as f:
            json.dump(obj.model_dump(), f, indent=2, default=str)

    def _load_all(self):
        """Load all memory objects from storage."""
        if not self.storage_path.exists():
            return
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    obj = MemoryObject(**data)
                    self.objects[obj.id] = obj
            except Exception:
                pass
