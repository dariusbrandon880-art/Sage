"""Read-only failure fingerprinting and repair qualification records."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
import re

_WS = re.compile(r"\s+")
_HEX = re.compile(r"\b[0-9a-f]{7,64}\b", re.I)
_NUM = re.compile(r"\b\d+\b")

def normalize_failure(message: str) -> str:
    if not isinstance(message, str) or not message.strip():
        raise ValueError("failure message required")
    return _NUM.sub("#", _HEX.sub("<sha>", _WS.sub(" ", message.strip()))).lower()

def failure_fingerprint(command: str, message: str) -> str:
    if not command.strip():
        raise ValueError("command required")
    payload = {"command": command.strip(), "message": normalize_failure(message)}
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

@dataclass(frozen=True)
class FailureObservation:
    fingerprint: str
    command: str
    message: str
    commit_sha: str
    surface: str
    exit_code: int

    def __post_init__(self):
        if len(self.fingerprint) != 64 or not all(c in "0123456789abcdef" for c in self.fingerprint):
            raise ValueError("invalid fingerprint")
        if not self.command.strip() or not self.commit_sha.strip() or not self.surface.strip():
            raise ValueError("required provenance missing")
        if self.exit_code == 0:
            raise ValueError("failure observation cannot have zero exit code")

@dataclass(frozen=True)
class RepairQualification:
    fingerprint: str
    repair_sha: str
    descendant_sha: str
    qualified: bool
    evidence_ref: str

    def __post_init__(self):
        if not self.fingerprint or not self.repair_sha or not self.descendant_sha or not self.evidence_ref:
            raise ValueError("qualification provenance missing")
        if self.qualified and self.repair_sha == self.descendant_sha:
            raise ValueError("qualification requires descendant evidence")

def collapse(observations: list[FailureObservation]) -> dict[str, tuple[FailureObservation, ...]]:
    grouped: dict[str, list[FailureObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.fingerprint, []).append(observation)
    return {key: tuple(value) for key, value in sorted(grouped.items())}
