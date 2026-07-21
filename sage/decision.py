"""Decision tracking system for SAGE."""

import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict

from sage.models import DecisionEntry, DecisionType


class DecisionTracker:
    """Tracks and persists all system decisions with rationale, evidence, and outcomes."""

    def __init__(self, storage_path: str = "sage_data/decisions"):
        """Initialize Decision Tracker.

        Args:
            storage_path: Path to store decision logs
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.decisions: Dict[str, DecisionEntry] = {}
        self._load_all_decisions()

    def record_decision(
        self,
        decision_type: DecisionType,
        description: str,
        rationale: str,
        evidence: Optional[List[str]] = None,
        decision_id: Optional[str] = None
    ) -> str:
        """Record a new decision.

        Args:
            decision_type: Type of decision
            description: Description of the decision
            rationale: Rationale behind the decision
            evidence: Supporting evidence list
            decision_id: Optional existing ID

        Returns:
            ID of the recorded decision
        """
        dec_id = decision_id or str(uuid.uuid4())
        entry = DecisionEntry(
            id=dec_id,
            decision_type=decision_type,
            description=description,
            rationale=rationale,
            evidence=evidence or []
        )

        self.decisions[dec_id] = entry
        self._save_decision(entry)

        return dec_id

    def retrieve_decision(self, decision_id: str) -> Optional[DecisionEntry]:
        """Retrieve a decision by ID.

        Args:
            decision_id: Unique decision ID

        Returns:
            DecisionEntry if found, None otherwise
        """
        if decision_id in self.decisions:
            return self.decisions[decision_id]

        # Try loading from disk
        filepath = self.storage_path / f"{decision_id}.json"
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    entry = DecisionEntry(**data)
                    self.decisions[decision_id] = entry
                    return entry
            except Exception:
                pass

        return None

    def list_all(self) -> List[DecisionEntry]:
        """List all tracked decisions.

        Returns:
            List of all DecisionEntry objects
        """
        return list(self.decisions.values())

    def _save_decision(self, entry: DecisionEntry):
        """Persist decision entry to disk."""
        filepath = self.storage_path / f"{entry.id}.json"
        with open(filepath, 'w') as f:
            json.dump(entry.model_dump(), f, indent=2, default=str)

    def _load_all_decisions(self):
        """Load all persisted decisions from storage."""
        if not self.storage_path.exists():
            return

        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    entry = DecisionEntry(**data)
                    self.decisions[entry.id] = entry
            except Exception:
                pass
