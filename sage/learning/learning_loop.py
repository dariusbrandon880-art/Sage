"""SAGE Learning Runtime - Governed Learning Loop Orchestrator."""

import json
from pathlib import Path
from typing import Any, Dict, List
from sage.learning.knowledge_candidate import KnowledgeCandidate
from sage.learning.intake import LearningIntake
from sage.learning.pattern_extractor import PatternExtractor
from sage.learning.validation_router import ValidationRouter


class GovernedLearningLoop:
    """Orchestrates SAGE's first governed learning pipeline loop."""

    def __init__(self, runtime: Any, persist_path: str | Path | None = None):
        self.runtime = runtime
        self.persist_path = Path(persist_path or runtime.workspace_path / "learned_candidates.json")
        self.intake = LearningIntake(runtime)
        self.pattern_extractor = PatternExtractor()
        self.validation_router = ValidationRouter(runtime)
        self.candidates: Dict[str, KnowledgeCandidate] = {}
        self.load_candidates()

    def process_incoming_event(self, source: str, event_data: Dict[str, Any], initial_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Run the complete pipeline from intake through extraction and validation routing."""
        results = []

        raw_candidate = self.intake.ingest_fact(source, event_data, initial_confidence)
        self.candidates[raw_candidate.candidate_id] = raw_candidate

        extracted_patterns = self.pattern_extractor.extract_patterns(raw_candidate)

        for pattern_cand in extracted_patterns:
            self.candidates[pattern_cand.candidate_id] = pattern_cand

            approved, msg = self.validation_router.route_to_validation(pattern_cand)
            results.append({
                "candidate_id": pattern_cand.candidate_id,
                "approved": approved,
                "message": msg,
                "validation_state": pattern_cand.validation_state,
                "promotion_status": pattern_cand.promotion_status,
            })

        self.save_candidates()
        return results

    def load_candidates(self) -> None:
        """Load learned candidates from disk to preserve state across restarts."""
        if not self.persist_path.exists():
            return
        try:
            with open(self.persist_path, "r") as f:
                data = json.load(f)
                for c_id, item in data.items():
                    self.candidates[c_id] = KnowledgeCandidate(**item)
        except Exception:
            pass

    def save_candidates(self) -> None:
        """Atomically persist candidates to disk."""
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.persist_path, "w") as f:
                json.dump({c_id: c.model_dump() for c_id, c in self.candidates.items()}, f, indent=2)
        except OSError:
            pass
