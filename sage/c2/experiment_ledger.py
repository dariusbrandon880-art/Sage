"""SAGE Experiment Ledger engine for tracking hypotheses, evidence, and validation decisions."""

from __future__ import annotations

from enum import Enum
import json
from pathlib import Path
import threading
import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Validation decision status for experiment records."""

    HOLD = "HOLD"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"


class ExperimentBaseline(BaseModel):
    """Baseline metrics and target thresholds for an experiment."""

    metric_name: str
    baseline_value: float
    target_value: float
    units: str = ""
    notes: str = ""


class CounterexampleRecord(BaseModel):
    """Record of a counterexample or falsifying condition observed during execution."""

    counterexample_id: str
    description: str
    discovered_at: float = Field(default_factory=time.time)
    impact_severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    evidence_ref: str = ""


class CandidateComparison(BaseModel):
    """Comparison record between a candidate technique and existing baseline."""

    candidate_id: str
    technique_name: str
    metric_name: str
    baseline_metric: float
    candidate_metric: float
    delta: float
    verdict: str = "INCONCLUSIVE"  # WIN, LOSS, INCONCLUSIVE


class AuthorizationRecord(BaseModel):
    """Explicit human/authority approval record required for promotion state transitions."""

    authorizer_id: str
    permission_scope: str
    evidence_hash: str
    notes: str = ""
    authorized_at: float = Field(default_factory=time.time)


class ExperimentRecord(BaseModel):
    """State-aware persistent experiment record binding hypothesis to evidence and decision."""

    experiment_id: str
    hypothesis: str
    wave_id: str
    flight_id: str
    commit_sha: str
    status: ValidationStatus = ValidationStatus.HOLD
    baselines: List[ExperimentBaseline] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    counterexamples: List[CounterexampleRecord] = Field(default_factory=list)
    candidate_comparisons: List[CandidateComparison] = Field(default_factory=list)
    authorization: Optional[AuthorizationRecord] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    validation_notes: str = ""


class ExperimentLedger:
    """Thread-safe persistent Experiment Ledger for SAGE concurrent wave execution."""

    def __init__(self, ledger_path: str = "evidence_capture/experiment_ledger.json"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._records: Dict[str, ExperimentRecord] = {}
        self._load_ledger()

    def _load_ledger(self) -> None:
        if self.ledger_path.exists():
            try:
                data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
                for rec_dict in data:
                    rec = ExperimentRecord.model_validate(rec_dict)
                    self._records[rec.experiment_id] = rec
            except Exception:
                self._records = {}

    def _save_ledger(self) -> None:
        payload = [rec.model_dump() for rec in self._records.values()]
        self.ledger_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def register_experiment(
        self,
        experiment_id: str,
        hypothesis: str,
        wave_id: str,
        flight_id: str,
        commit_sha: str,
        baselines: Optional[List[ExperimentBaseline]] = None,
        evidence_refs: Optional[List[str]] = None,
    ) -> ExperimentRecord:
        with self._lock:
            now = time.time()
            record = ExperimentRecord(
                experiment_id=experiment_id,
                hypothesis=hypothesis,
                wave_id=wave_id,
                flight_id=flight_id,
                commit_sha=commit_sha,
                status=ValidationStatus.HOLD,
                baselines=baselines or [],
                evidence_refs=evidence_refs or [],
                created_at=now,
                updated_at=now,
            )
            self._records[experiment_id] = record
            self._save_ledger()
            return record

    def bind_baseline(
        self, experiment_id: str, baseline: ExperimentBaseline
    ) -> ExperimentRecord:
        with self._lock:
            if experiment_id not in self._records:
                raise KeyError(f"Experiment {experiment_id} not found in ledger.")
            rec = self._records[experiment_id]
            rec.baselines.append(baseline)
            rec.updated_at = time.time()
            self._save_ledger()
            return rec

    def add_observation(self, experiment_id: str, observation: str) -> ExperimentRecord:
        with self._lock:
            if experiment_id not in self._records:
                raise KeyError(f"Experiment {experiment_id} not found in ledger.")
            rec = self._records[experiment_id]
            rec.observations.append(observation)
            rec.updated_at = time.time()
            self._save_ledger()
            return rec

    def add_evidence_ref(self, experiment_id: str, evidence_ref: str) -> ExperimentRecord:
        with self._lock:
            if experiment_id not in self._records:
                raise KeyError(f"Experiment {experiment_id} not found in ledger.")
            rec = self._records[experiment_id]
            if evidence_ref not in rec.evidence_refs:
                rec.evidence_refs.append(evidence_ref)
            rec.updated_at = time.time()
            self._save_ledger()
            return rec

    def add_counterexample(
        self, experiment_id: str, counterexample: CounterexampleRecord
    ) -> ExperimentRecord:
        with self._lock:
            if experiment_id not in self._records:
                raise KeyError(f"Experiment {experiment_id} not found in ledger.")
            rec = self._records[experiment_id]
            rec.counterexamples.append(counterexample)
            rec.updated_at = time.time()
            self._save_ledger()
            return rec

    def add_candidate_comparison(
        self, experiment_id: str, comparison: CandidateComparison
    ) -> ExperimentRecord:
        with self._lock:
            if experiment_id not in self._records:
                raise KeyError(f"Experiment {experiment_id} not found in ledger.")
            rec = self._records[experiment_id]
            rec.candidate_comparisons.append(comparison)
            rec.updated_at = time.time()
            self._save_ledger()
            return rec

    def attach_authorization(
        self, experiment_id: str, authorization: AuthorizationRecord
    ) -> ExperimentRecord:
        with self._lock:
            if experiment_id not in self._records:
                raise KeyError(f"Experiment {experiment_id} not found in ledger.")
            rec = self._records[experiment_id]
            rec.authorization = authorization
            rec.updated_at = time.time()
            self._save_ledger()
            return rec

    def update_validation_decision(
        self,
        experiment_id: str,
        status: ValidationStatus,
        notes: str = "",
        authorization: Optional[AuthorizationRecord] = None,
    ) -> ExperimentRecord:
        with self._lock:
            if experiment_id not in self._records:
                raise KeyError(f"Experiment {experiment_id} not found in ledger.")
            rec = self._records[experiment_id]

            if authorization:
                rec.authorization = authorization

            # Fail-closed evidence & explicit authorization verification for PROMOTED status
            if status == ValidationStatus.PROMOTED:
                if not rec.authorization:
                    rec.status = ValidationStatus.HOLD
                    rec.validation_notes = (
                        f"PROMOTION REJECTED: Missing explicit AuthorizationRecord. Defaulting to HOLD. {notes}".strip()
                    )
                    rec.updated_at = time.time()
                    self._save_ledger()
                    return rec

                if not rec.evidence_refs:
                    rec.status = ValidationStatus.HOLD
                    rec.validation_notes = (
                        f"PROMOTION REJECTED: Zero evidence refs attached. Defaulting to HOLD. {notes}".strip()
                    )
                    rec.updated_at = time.time()
                    self._save_ledger()
                    return rec

                for ref in rec.evidence_refs:
                    if not Path(ref).exists():
                        rec.status = ValidationStatus.HOLD
                        rec.validation_notes = (
                            f"PROMOTION REJECTED: Evidence ref {ref} missing on disk. Defaulting to HOLD. {notes}".strip()
                        )
                        rec.updated_at = time.time()
                        self._save_ledger()
                        return rec

            rec.status = status
            rec.validation_notes = notes
            rec.updated_at = time.time()
            self._save_ledger()
            return rec

    def record_flight_receipt(
        self, wave_id: str, flight_id: str, commit_sha: str, receipt_data: dict
    ) -> ExperimentRecord:
        exp_id = f"exp_{wave_id}_{flight_id}"
        with self._lock:
            evidence_ref = receipt_data.get("evidence_ref", "")
            target_path = receipt_data.get("target_path", flight_id)
            status_str = receipt_data.get("status", "PASS")

            if exp_id in self._records:
                rec = self._records[exp_id]
            else:
                rec = ExperimentRecord(
                    experiment_id=exp_id,
                    hypothesis=f"Flight {flight_id} target {target_path} achieves verified execution proof.",
                    wave_id=wave_id,
                    flight_id=flight_id,
                    commit_sha=commit_sha,
                    status=ValidationStatus.HOLD,
                )
                self._records[exp_id] = rec

            rec.observations.append(f"Flight status: {status_str} at head {commit_sha}")
            if evidence_ref and evidence_ref not in rec.evidence_refs:
                rec.evidence_refs.append(evidence_ref)
            rec.updated_at = time.time()

            # Fail-closed governance invariant:
            # EXECUTION -> EVIDENCE -> VERIFY -> VALIDATE -> AUTHORIZATION -> PROMOTE -> IMMERSION
            # Receipts attach evidence/observations but MUST maintain ValidationStatus.HOLD.
            rec.status = ValidationStatus.HOLD
            rec.validation_notes = "Receipt recorded. Awaiting formal validation & explicit authorization."

            self._save_ledger()
            return rec

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        with self._lock:
            return self._records.get(experiment_id)

    def list_experiments(self) -> List[ExperimentRecord]:
        with self._lock:
            return list(self._records.values())
