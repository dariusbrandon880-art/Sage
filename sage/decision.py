"""Decision tracking system for recording engineering decisions and lineages."""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from sage.models import DecisionEntry, DecisionType


class DecisionTracker:
    """Tracker for documenting and persisting engineering and design decisions."""

    def __init__(self, storage_path: str = "sage_data/decisions"):
        """Initialize decision tracker.

        Args:
            storage_path: Directory path for persisting decisions.
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
        evidence: Optional[List[str]] = None
    ) -> str:
        """Record an engineering or design decision with rationale and evidence.

        Args:
            decision_type: The type/category of the decision.
            description: Description of the decision made.
            rationale: Rationale or context justifying the decision.
            evidence: Optional list of supporting evidence files, tests, or references.

        Returns:
            The generated decision ID.
        """
        decision = DecisionEntry(
            decision_type=decision_type,
            description=description,
            rationale=rationale,
            evidence=evidence or []
        )

        self.decisions[decision.id] = decision
        self._save_decision(decision)
        return decision.id

    def list_all(self) -> List[DecisionEntry]:
        """List all tracked decisions.

        Returns:
            A list of all DecisionEntry instances.
        """
        return list(self.decisions.values())

    def retrieve_decision(self, decision_id: str) -> Optional[DecisionEntry]:
        """Retrieve a decision by its ID.

        Args:
            decision_id: The ID of the decision to retrieve.

        Returns:
            The DecisionEntry instance if found, else None.
        """
        if decision_id in self.decisions:
            return self.decisions[decision_id]

        # Fallback to load from disk
        filepath = self.storage_path / f"{decision_id}.json"
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    decision = DecisionEntry(**data)
                    self.decisions[decision_id] = decision
                    return decision
            except Exception:
                pass

        return None

    def _save_decision(self, decision: DecisionEntry) -> None:
        """Persist a single decision to disk."""
        filepath = self.storage_path / f"{decision.id}.json"
        with open(filepath, "w") as f:
            json.dump(decision.model_dump(), f, indent=2, default=str)

    def _load_all_decisions(self) -> None:
        """Load all saved decisions from storage path."""
        if not self.storage_path.exists():
            return

        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    decision = DecisionEntry(**data)
                    self.decisions[decision.id] = decision
            except Exception as e:
                print(f"Error loading decision from {filepath}: {e}")

    def export_state(self) -> Dict[str, Any]:
        """Export current decisions state.

        Returns:
            A dictionary summary of all decisions.
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_count": len(self.decisions),
            "decisions": [d.model_dump() for d in self.decisions.values()]
        }
