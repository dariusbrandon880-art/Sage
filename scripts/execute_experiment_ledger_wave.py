#!/usr/bin/env python3
"""Execute a governed Big Jump Wave and persist its observations to the Experiment Ledger.

This runner deliberately does not synthesize a superiority claim. It executes the
existing five-flight wave, records each observed flight with exact Git provenance,
and emits a HOLD when no independently measured competing technique is supplied.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from sage.c2.build_jump_wave import BuildJumpWaveEngine  # noqa: E402
from sage.c2.experiment_ledger import ExperimentLedger, ExperimentTrial  # noqa: E402
from sage.c2.evolution_loop import FitnessVector, EvolutionDecision, EvolutionLoop  # noqa: E402

EVIDENCE_PATH = repo_root / "evidence_capture" / "experiment_ledger_wave_evidence.json"


def _observed_fitness(success: bool, tests_passed: int) -> FitnessVector:
    """Encode only directly observed execution facts; no superiority is inferred."""
    correctness = 1.0 if success else 0.0
    evidence_quality = 1.0 if success else 0.0
    repeatability = 0.0
    recovery = 1.0 if success else 0.0
    generalization = 0.0
    mission_value = 1.0 if success else 0.0
    cost = 1.0 / max(1, tests_passed)
    return FitnessVector(
        mission_value=mission_value,
        correctness=correctness,
        repeatability=repeatability,
        evidence_quality=evidence_quality,
        recovery=recovery,
        generalization=generalization,
        cost=cost,
    )


def main() -> int:
    print("=" * 70)
    print("SAGE C2 EXPERIMENT LEDGER — BIG JUMP WAVE")
    print("=" * 70)

    engine = BuildJumpWaveEngine(storage_dir=str(repo_root / "evidence_capture"))
    wave_id = f"wave-experiment-ledger-{int(time.time())}"
    package = engine.execute_wave(wave_id=wave_id)
    head_sha = engine.get_current_head_sha()

    ledger = ExperimentLedger()
    for summary in package.flight_summaries:
        ledger.append(
            ExperimentTrial(
                mission_id=wave_id,
                technique_id="big-jump-wave-v1-observed",
                trial_id=f"{wave_id}:{summary.flight_id}",
                fitness=_observed_fitness(
                    summary.execution_result == "PASS", summary.tests_passed
                ),
                evidence_ref=summary.evidence_ref,
                exact_git_head=summary.exact_head,
                adversarial=False,
                regression_free=summary.execution_result == "PASS",
                human_reviewed=False,
            )
        )

    # A single observed technique is evidence capture, not a comparative experiment.
    # Constructing a baseline from it is permitted; evaluation remains HOLD because
    # there is no independent competing technique with the required gates.
    baseline = ledger.build_baseline(wave_id, "big-jump-wave-v1-observed")
    evaluation = EvolutionLoop().evaluate(wave_id, baseline, [])

    package_dict = package.model_dump()
    output = {
        "wave": package_dict,
        "ledger_trials": json.loads(ledger.export_json()),
        "baseline": baseline.model_dump(),
        "evolution_evaluation": evaluation.model_dump(mode="json"),
        "promotion_authorized": evaluation.promotion_authorized,
        "exact_git_head": head_sha,
        "execution_classification": "OBSERVATION_ONLY",
        "superiority_claim": False,
        "verdict": "HOLD",
        "reason": "Wave observations captured, but no independently measured competing technique was supplied.",
    }

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"Wave ID: {wave_id}")
    print(f"Exact Git HEAD: {head_sha}")
    print(f"Flights observed: {len(package.flight_summaries)}")
    print(f"Ledger trials: {len(json.loads(ledger.export_json()))}")
    print(f"Evolution decision: {evaluation.decision.value}")
    print(f"Promotion authorized: {evaluation.promotion_authorized}")
    print(f"Evidence: {EVIDENCE_PATH}")

    # Observation capture succeeded; HOLD is the correct scientific/governance result.
    return 0 if evaluation.decision is EvolutionDecision.HOLD else 1


if __name__ == "__main__":
    raise SystemExit(main())
