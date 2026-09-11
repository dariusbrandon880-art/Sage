"""Blind Scenario Layer for AIET.

Represents unseen, controlled evaluation environments and tasks against which
baseline and candidate operational techniques are benchmarked without lookahead.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class AIETBlindScenario(BaseModel):
    """A blind evaluation scenario with inputs, environmental dynamics, and expected invariants."""

    scenario_id: str
    description: str
    domain: str
    difficulty_level: str = "MAJOR"  # ROUTINE, MAJOR, CRITICAL
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_invariants: List[str] = Field(default_factory=list)
    transfer_target_domain: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def validate_invariants(self, output: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Verify output against expected scenario invariants."""
        violations: List[str] = []
        for invariant in self.expected_invariants:
            if invariant.startswith("KEY_EXISTS:"):
                key = invariant.split("KEY_EXISTS:")[1].strip()
                if key not in output:
                    violations.append(f"MISSING_KEY:{key}")
            elif invariant.startswith("NON_EMPTY:"):
                key = invariant.split("NON_EMPTY:")[1].strip()
                if not output.get(key):
                    violations.append(f"EMPTY_VALUE:{key}")
            elif invariant.startswith("GTE:"):
                parts = invariant.split(":")
                if len(parts) == 3:
                    key, val_str = parts[1].strip(), parts[2].strip()
                    val = float(val_str)
                    if float(output.get(key, 0)) < val:
                        violations.append(f"INVARIANT_BELOW_THRESHOLD:{key}<{val}")
        return len(violations) == 0, violations
