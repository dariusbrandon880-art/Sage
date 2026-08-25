"""Flight A: Directive Fidelity & Exact-Order Sentinel for SAGE C2.

Provides deterministic parsing, fingerprinting, requirement origin tracking,
and strict order validation for user instructions to prevent unauthorized plan
additions, order shuffling, or paraphrasing into different missions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class RequirementOrigin:
    source_type: str  # "user_directive", "repository_governance", "explicit_safety_constraint", "validated_dependency"
    source_id: str
    directive_position: int
    authorization: str  # "authorized", "unauthorized"


@dataclass(frozen=True)
class ActionStep:
    step_number: int
    action: str
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    origin: Optional[RequirementOrigin] = None


@dataclass(frozen=True)
class DirectiveContract:
    directive_id: str
    raw_instruction: str
    raw_instruction_hash: str
    ordered_actions: Tuple[ActionStep, ...]
    explicit_constraints: Tuple[str, ...]
    forbidden_additions: Tuple[str, ...]
    required_sources: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "directive_id": self.directive_id,
            "raw_instruction": self.raw_instruction,
            "raw_instruction_hash": self.raw_instruction_hash,
            "ordered_actions": [asdict(a) for a in self.ordered_actions],
            "explicit_constraints": list(self.explicit_constraints),
            "forbidden_additions": list(self.forbidden_additions),
            "required_sources": list(self.required_sources),
        }


@dataclass(frozen=True)
class DirectiveFidelityValidationResult:
    is_valid: bool
    violations: Tuple[str, ...]
    contract_hash: str


class DirectiveFingerprint:
    """Parses raw user instructions into a canonical DirectiveContract with SHA-256 fingerprinting and origin tracking."""

    @staticmethod
    def compute_hash(raw_text: str) -> str:
        return hashlib.sha256(raw_text.strip().encode("utf-8")).hexdigest()

    @classmethod
    def create_contract(
        cls,
        raw_instruction: str,
        directive_id: str = "dir-001",
    ) -> DirectiveContract:
        raw_hash = cls.compute_hash(raw_instruction)
        lines = [line.strip() for line in raw_instruction.splitlines() if line.strip()]

        actions: List[ActionStep] = []
        constraints: List[str] = []
        forbidden: List[str] = []
        sources: List[str] = []

        step_counter = 1
        for line in lines:
            lower = line.lower()
            if lower.startswith(("do not ", "don't ", "never ", "must not ")):
                constraints.append(line)
                forbidden_term = re.sub(r"^(do not|don't|never|must not)\s+", "", line, flags=re.IGNORECASE).strip().rstrip(".")
                forbidden.append(forbidden_term)
            elif lower.startswith(("check live", "check github", "inspect", "run", "verify", "execute", "list", "read", "fetch")):
                origin = RequirementOrigin(
                    source_type="user_directive",
                    source_id=directive_id,
                    directive_position=step_counter,
                    authorization="authorized",
                )
                actions.append(ActionStep(step_number=step_counter, action=line, origin=origin))
                step_counter += 1
                if "github" in lower or "repo" in lower:
                    if "github" not in sources:
                        sources.append("github")
                if "file" in lower or "codebase" in lower:
                    if "filesystem" not in sources:
                        sources.append("filesystem")
            elif any(k in lower for k in ["check", "inspect", "run", "verify", "execute", "merge", "commit"]):
                origin = RequirementOrigin(
                    source_type="user_directive",
                    source_id=directive_id,
                    directive_position=step_counter,
                    authorization="authorized",
                )
                actions.append(ActionStep(step_number=step_counter, action=line, origin=origin))
                step_counter += 1

        return DirectiveContract(
            directive_id=directive_id,
            raw_instruction=raw_instruction,
            raw_instruction_hash=raw_hash,
            ordered_actions=tuple(actions),
            explicit_constraints=tuple(constraints),
            forbidden_additions=tuple(forbidden),
            required_sources=tuple(sources),
        )


class ExactOrderSentinel:
    """Validates proposed C2 execution plans against a canonical DirectiveContract."""

    @staticmethod
    def validate_plan(
        contract: DirectiveContract,
        proposed_plan_actions: Sequence[str | ActionStep],
    ) -> DirectiveFidelityValidationResult:
        violations: List[str] = []

        # 1. Check for forbidden additions in proposed actions
        for action_item in proposed_plan_actions:
            action_str = action_item.action if isinstance(action_item, ActionStep) else str(action_item)
            lower_action = action_str.lower().strip().rstrip(".")

            # Origin check if passed as ActionStep
            if isinstance(action_item, ActionStep) and action_item.origin:
                if action_item.origin.authorization != "authorized":
                    violations.append(f"Action '{action_str}' possesses unauthorized requirement origin: {action_item.origin}")

            for forbidden in contract.forbidden_additions:
                forbidden_clean = forbidden.lower().strip().rstrip(".")
                if forbidden_clean in lower_action:
                    violations.append(
                        f"Forbidden action addition detected in plan: '{action_str}' violates constraint '{forbidden}'"
                    )

        # 2. Check action sequence alignment & order
        contract_actions_clean = [a.action.lower().strip().rstrip(".") for a in contract.ordered_actions]

        contract_idx = 0
        for proposed_item in proposed_plan_actions:
            proposed_action = proposed_item.action if isinstance(proposed_item, ActionStep) else str(proposed_item)
            lower_prop = proposed_action.lower().strip().rstrip(".")

            # Check if this proposed action matches any forbidden additions
            is_forbidden = any(f.lower().strip().rstrip(".") in lower_prop for f in contract.forbidden_additions)
            if is_forbidden:
                continue

            # Check if proposed action matches expected next contract action
            if contract_idx < len(contract_actions_clean):
                expected = contract_actions_clean[contract_idx]
                expected_words = [w for w in expected.split() if len(w) > 2]
                if expected == lower_prop or any(word in lower_prop for word in expected_words):
                    contract_idx += 1
                else:
                    violations.append(
                        f"Plan step '{proposed_action}' does not align with canonical directive step '{contract.ordered_actions[contract_idx].action}'"
                    )
            else:
                violations.append(
                    f"Unauthorized excess step proposed beyond canonical directive: '{proposed_action}'"
                )

        is_valid = len(violations) == 0
        contract_hash = contract.raw_instruction_hash

        return DirectiveFidelityValidationResult(
            is_valid=is_valid,
            violations=tuple(violations),
            contract_hash=contract_hash,
        )
