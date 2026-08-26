"""Directive fidelity and exact-order validation for governed C2 execution."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import hashlib
import re
from typing import Any, Dict, Optional, Sequence, Tuple, List

@dataclass(frozen=True)
class RequirementOrigin:
    source_type: str
    source_id: str
    directive_position: int
    authorization: str

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
        return {"directive_id": self.directive_id, "raw_instruction": self.raw_instruction, "raw_instruction_hash": self.raw_instruction_hash, "ordered_actions": [asdict(a) for a in self.ordered_actions], "explicit_constraints": list(self.explicit_constraints), "forbidden_additions": list(self.forbidden_additions), "required_sources": list(self.required_sources)}

@dataclass(frozen=True)
class DirectiveFidelityValidationResult:
    is_valid: bool
    violations: Tuple[str, ...]
    contract_hash: str

class DirectiveFingerprint:
    @staticmethod
    def compute_hash(raw_text: str) -> str:
        return hashlib.sha256(raw_text.strip().encode()).hexdigest()
    @classmethod
    def create_contract(cls, raw_instruction: str, directive_id: str = "dir-001") -> DirectiveContract:
        actions: List[ActionStep] = []
        constraints: List[str] = []
        forbidden: List[str] = []
        sources: List[str] = []
        step = 1
        for line in [line.strip() for line in raw_instruction.splitlines() if line.strip()]:
            lower = line.lower()
            if lower.startswith(("do not ", "don't ", "never ", "must not ")):
                constraints.append(line)
                forbidden.append(re.sub(r"^(do not|don't|never|must not)\s+", "", line, flags=re.I).rstrip("."))
            elif lower.startswith(("check", "inspect", "run", "verify", "execute", "list", "read", "fetch", "merge", "commit")):
                actions.append(ActionStep(step, line, origin=RequirementOrigin("user_directive", directive_id, step, "authorized")))
                step += 1
                if "github" in lower or "repo" in lower: sources.append("github") if "github" not in sources else None
                if "file" in lower or "codebase" in lower: sources.append("filesystem") if "filesystem" not in sources else None
        return DirectiveContract(directive_id, raw_instruction, cls.compute_hash(raw_instruction), tuple(actions), tuple(constraints), tuple(forbidden), tuple(sources))

class ExactOrderSentinel:
    @staticmethod
    def validate_plan(contract: DirectiveContract, proposed_plan_actions: Sequence[str | ActionStep]) -> DirectiveFidelityValidationResult:
        violations: List[str] = []
        expected = [a.action.lower().strip().rstrip(".") for a in contract.ordered_actions]
        idx = 0
        for item in proposed_plan_actions:
            text = item.action if isinstance(item, ActionStep) else str(item)
            lower = text.lower().strip().rstrip(".")
            if isinstance(item, ActionStep) and item.origin and item.origin.authorization != "authorized":
                violations.append(f"Action '{text}' possesses unauthorized requirement origin")
            if any(f.lower().strip().rstrip(".") in lower for f in contract.forbidden_additions):
                violations.append(f"Forbidden action addition detected in plan: '{text}'")
                continue
            if idx >= len(expected):
                violations.append(f"Unauthorized excess step proposed beyond canonical directive: '{text}'")
                continue
            if lower == expected[idx] or any(word in lower for word in expected[idx].split() if len(word) > 2):
                idx += 1
            else:
                violations.append(f"Plan step '{text}' does not align with canonical directive step '{contract.ordered_actions[idx].action}'")
        return DirectiveFidelityValidationResult(not violations, tuple(violations), contract.raw_instruction_hash)
