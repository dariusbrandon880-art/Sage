"""Cognitive State Persistence & Rehydration Manager.

Provides deterministic, schema-validated persistence and cross-session fresh-process
rehydration for SAGE CognitiveState and provenance evidence without conversational memory dependencies.
"""

import json
from pathlib import Path
from typing import Union
from pydantic import BaseModel

from sage.experimental.cognitive.state_schema import CognitiveState


class CognitivePersistenceManager:
    """Manages deterministic saving and fresh-process rehydration of CognitiveState."""

    def __init__(
        self,
        ledger_path: Union[str, Path] = "evidence_capture/cognitive_state_ledger.json"
    ):
        self.ledger_path = Path(ledger_path)

    def save_state(self, state: CognitiveState) -> Path:
        """Persist CognitiveState deterministically to disk in UTF-8 JSON format."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = state.model_dump_json(indent=2)
        with open(self.ledger_path, "w", encoding="utf-8") as f:
            f.write(serialized)
        return self.ledger_path

    def load_state(self) -> CognitiveState:
        """Rehydrate CognitiveState directly from disk in a fresh process."""
        if not self.ledger_path.exists():
            raise FileNotFoundError(f"Cognitive state ledger path '{self.ledger_path}' does not exist.")

        with open(self.ledger_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return CognitiveState.model_validate(data)
