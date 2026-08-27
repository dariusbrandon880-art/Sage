"""Executable mission contracts for SAGE C2.

This module is intentionally small and stdlib-only. It turns the high-tempo
execution doctrine's most deterministic boundaries into executable checks
without creating a second authority model.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "1.0"


class MissionContractError(ValueError):
    """Raised when a mission contract is malformed or unsafe."""


@dataclass(frozen=True)
class MissionContract:
    """Validated, immutable mission boundary used by execution tooling."""

    mission_id: str
    intent: str
    allowed_paths: tuple[str, ...] = ()
    prohibited_paths: tuple[str, ...] = ()
    required_tests: tuple[str, ...] = ()
    stop_the_line_conditions: tuple[str, ...] = ()
    provenance_required: bool = True
    min_coverage_pct: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MissionContract":
        if payload.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
            raise MissionContractError("Unsupported mission contract schema version")

        mission_id = payload.get("mission_id")
        intent = payload.get("intent")
        if not isinstance(mission_id, str) or not mission_id.strip():
            raise MissionContractError("mission_id must be a non-empty string")
        if not isinstance(intent, str) or not intent.strip():
            raise MissionContractError("intent must be a non-empty string")

        boundary = payload.get("authority_boundary", {})
        completion = payload.get("completion_criteria", {})
        if not isinstance(boundary, Mapping) or not isinstance(completion, Mapping):
            raise MissionContractError("authority_boundary and completion_criteria must be objects")

        allowed = _string_tuple(boundary.get("allowed_paths", []), "allowed_paths")
        prohibited = _string_tuple(boundary.get("prohibited_paths", []), "prohibited_paths")
        tests = _string_tuple(completion.get("required_tests", []), "required_tests")
        stops = _string_tuple(payload.get("stop_the_line_conditions", []), "stop_the_line_conditions")

        coverage = completion.get("min_coverage_pct")
        if coverage is not None:
            if not isinstance(coverage, (int, float)) or isinstance(coverage, bool) or not 0 <= coverage <= 100:
                raise MissionContractError("min_coverage_pct must be a number from 0 to 100")
            coverage = float(coverage)

        provenance = completion.get("provenance_required", True)
        if not isinstance(provenance, bool):
            raise MissionContractError("provenance_required must be boolean")

        return cls(
            mission_id=mission_id.strip(),
            intent=intent.strip(),
            allowed_paths=allowed,
            prohibited_paths=prohibited,
            required_tests=tests,
            stop_the_line_conditions=stops,
            provenance_required=provenance,
            min_coverage_pct=coverage,
            metadata=dict(payload.get("metadata", {})) if isinstance(payload.get("metadata", {}), Mapping) else {},
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "MissionContract":
        with Path(path).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, Mapping):
            raise MissionContractError("Mission contract root must be a JSON object")
        return cls.from_mapping(payload)

    def check_paths(self, paths: Iterable[str | Path]) -> tuple[str, ...]:
        """Return violations for paths outside the declared mission boundary."""
        violations: list[str] = []
        for raw_path in paths:
            path = Path(raw_path).as_posix().lstrip("./")
            if any(_matches(path, pattern) for pattern in self.prohibited_paths):
                violations.append(f"PROHIBITED_PATH:{path}")
                continue
            if self.allowed_paths and not any(_matches(path, pattern) for pattern in self.allowed_paths):
                violations.append(f"OUTSIDE_BOUNDARY:{path}")
        return tuple(violations)

    def requires_stop(self, conditions: Iterable[str]) -> tuple[str, ...]:
        """Return declared stop-the-line conditions observed in a run."""
        declared = set(self.stop_the_line_conditions)
        return tuple(condition for condition in conditions if condition in declared)

    def completion_gates(self) -> dict[str, Any]:
        return {
            "required_tests": self.required_tests,
            "min_coverage_pct": self.min_coverage_pct,
            "provenance_required": self.provenance_required,
        }


def validate_contract_file(path: str | Path) -> MissionContract:
    """Load and validate a mission contract from JSON."""
    return MissionContract.from_file(path)


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise MissionContractError(f"{field_name} must be a list of non-empty strings")
    return tuple(item.strip() for item in value)


def _matches(path: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/").lstrip("./")
    if normalized.endswith("/**"):
        prefix = normalized[:-3].rstrip("/")
        return path == prefix or path.startswith(prefix + "/")
    if normalized.endswith("/*"):
        prefix = normalized[:-2].rstrip("/")
        return path == prefix or (path.startswith(prefix + "/") and "/" not in path[len(prefix) + 1 :])
    return fnmatch.fnmatchcase(path, normalized)
