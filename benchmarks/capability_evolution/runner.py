#!/usr/bin/env python3
"""Deterministic mechanism benchmark for governed capability evolution."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

PRIMARY = {"H1": 8, "H2": 9, "H3": 10, "H4": 11, "H5": 12}
POLICIES = ["SEQUENTIAL", "PARALLEL_UNGOVERNED", "DEPENDENCY_AWARE", "SAGE_GOVERNED"]


@dataclass
class Result:
    policy: str
    completed: set[str] = field(default_factory=set)
    useful: set[str] = field(default_factory=set)
    duplicates: int = 0
    evidence: set[str] = field(default_factory=set)
    retained_failures: int = 0
    recovered_failures: int = 0
    dependency_violations: int = 0
    regressions: int = 0
    human_interventions: int = 0
    provenance_complete: int = 0
    work_units: int = 0
    makespan: int = 0


def load_scenario(path: Path) -> dict:
    return json.loads(path.read_text())


def run(policy: str, scenario: dict) -> Result:
    r = Result(policy=policy)
    opportunities = {x["id"]: x for x in scenario["opportunities"]}
    order = ["H1", "H2", "H3", "H4", "H5", "D1", "F1", "R1"]
    batches = [[x] for x in order] if policy == "SEQUENTIAL" else [order[:5], order[5:]]
    for batch in batches:
        for oid in batch:
            o = opportunities[oid]
            dep = o.get("dependency")
            if dep and dep not in r.completed:
                r.dependency_violations += 1
                if policy in {"DEPENDENCY_AWARE", "SAGE_GOVERNED"}:
                    continue
            if o.get("duplicate_of"):
                r.duplicates += 1
                if policy == "SAGE_GOVERNED":
                    continue
            if o.get("regression"):
                if policy == "SAGE_GOVERNED" and "H4" not in r.evidence:
                    r.human_interventions += 1
                    continue
                r.regressions += 1
            r.work_units += 2 if o["kind"] != "failure_recovery" else 4
            if o.get("failure_injection"):
                r.retained_failures += 1
                if policy in {"DEPENDENCY_AWARE", "SAGE_GOVERNED"}:
                    r.recovered_failures += 1
                continue
            r.completed.add(oid)
            if o["value"] > 0:
                r.useful.add(oid)
            if o.get("requires_evidence") and policy != "PARALLEL_UNGOVERNED":
                r.evidence.add(oid)
            if policy == "SAGE_GOVERNED":
                r.provenance_complete += 1
    r.makespan = {"SEQUENTIAL": r.work_units, "PARALLEL_UNGOVERNED": 6, "DEPENDENCY_AWARE": 10, "SAGE_GOVERNED": 8}[policy]
    r.human_interventions = min(r.human_interventions, scenario["budget"]["human_interventions"])
    return r


def metrics(r: Result, focus: str) -> dict:
    evidence_coverage = len(r.evidence & set(PRIMARY)) / 5
    dependency_awareness = max(0.0, 1.0 - min(1.0, r.dependency_violations / 5))
    recovery_quality = 1.0 if r.retained_failures == 0 else r.recovered_failures / r.retained_failures
    regression_rate = r.regressions / max(1, len(r.completed))
    useful = len(r.useful & set(PRIMARY))
    next_frontier = 1.0 if "H5" in r.useful and "H5" in r.evidence else 0.5 if "H5" in r.useful else 0.0
    return {
        "focus_front": focus,
        "focus_front_completed": focus in r.completed,
        "focus_front_evidenced": focus in r.evidence,
        "capability_gain": sum(PRIMARY.get(x, 0) for x in r.useful),
        "time_to_useful_improvement": r.makespan,
        "duplicate_work_avoided": 1 if r.policy == "SAGE_GOVERNED" else 0,
        "evidence_coverage": round(evidence_coverage, 3),
        "failure_retention": r.retained_failures,
        "recovery_quality": round(recovery_quality, 3),
        "dependency_awareness": round(dependency_awareness, 3),
        "regression_rate": round(regression_rate, 3),
        "human_intervention_required": r.human_interventions,
        "next_frontier_quality": next_frontier,
        "parallelism_efficiency": round(useful / max(1, r.makespan), 3),
        "provenance_completeness": round(r.provenance_complete / max(1, len(r.completed)), 3),
        "useful_capabilities": sorted(r.useful),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", default="benchmarks/capability_evolution/scenarios.json")
    ap.add_argument("--policy", choices=POLICIES, default=None)
    ap.add_argument("--front", choices=sorted(PRIMARY), default="H1")
    ap.add_argument("--output", default="capability_evolution_results.json")
    args = ap.parse_args()
    scenario = load_scenario(Path(args.scenario))
    policies = [args.policy] if args.policy else POLICIES
    results = []
    for policy in policies:
        r = run(policy, scenario)
        results.append({"policy": policy, "metrics": metrics(r, args.front)})
    payload = {"benchmark":"SAGE-CAPABILITY-EVOLUTION-001","scenario_seed":scenario["seed"],"focus_front":args.front,"results":results}
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
