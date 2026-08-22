"""Native loader for persisted SAGE ArchiveEntry evidence.

Read-only: it never promotes, mutates, or authorizes canonical state.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sage.models import ArchiveEntry


class NativePersistedEvidenceLoader:
    """Load persisted ArchiveEntry JSON with fail-closed validation."""

    def __init__(self, root: str | Path = "sage_data/archive") -> None:
        self.root = Path(root)

    def load_file(self, path: str | Path) -> ArchiveEntry:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        if not candidate.is_file():
            raise FileNotFoundError(f"Persisted evidence not found: {candidate}")
        try:
            raw: Any = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Persisted evidence is not valid JSON: {candidate}") from exc
        if isinstance(raw, list):
            if len(raw) != 1:
                raise ValueError("Persisted evidence loader requires exactly one ArchiveEntry per file")
            raw = raw[0]
        if not isinstance(raw, dict):
            raise TypeError("Persisted evidence root must be an object")
        return ArchiveEntry.model_validate(raw)

    def load_all(self) -> list[ArchiveEntry]:
        if not self.root.exists():
            return []
        entries: list[ArchiveEntry] = []
        for path in sorted(self.root.glob("*.json")):
            entries.append(self.load_file(path))
        return entries

    def select(self, *, tag: str | None = None, knowledge_state: str | None = None) -> list[ArchiveEntry]:
        entries = self.load_all()
        return [
            entry for entry in entries
            if (tag is None or tag in entry.tags)
            and (knowledge_state is None or entry.knowledge_state.value == knowledge_state)
        ]
