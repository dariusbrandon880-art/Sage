"""Runner script executing Fleet Concurrency Engine and persisting SHA-256 evidence receipt."""
import sys
from pathlib import Path

# Bootstrap sys.path to include repo root
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import json
from sage.experimental.airspace.fleet_concurrency import (
    FleetConcurrencyEngine,
    FlightWorkUnit,
)

def main():
    engine = FleetConcurrencyEngine(max_concurrent_flights=10)
    sample_units = [
        FlightWorkUnit(
            flight_id="Flight A",
            mission_id="msn-concat-001",
            frontier_name="research_intelligence",
            namespace_boundary="sage.c2.dispatch.flight_a",
        ),
        FlightWorkUnit(
            flight_id="Flight B",
            mission_id="msn-concat-002",
            frontier_name="continuity_context",
            namespace_boundary="sage.c2.dispatch.flight_b",
            depends_on=("msn-concat-001",),
        ),
        FlightWorkUnit(
            flight_id="Flight C",
            mission_id="msn-concat-003",
            frontier_name="execution_substrate",
            namespace_boundary="sage.c2.dispatch.flight_c",
        ),
    ]

    result = engine.execute_concurrent_wave(dispatch_id="dispatch-wave-conc-001", units=sample_units)

    evidence_data = {
        "capability": "fleet_concurrency_engine",
        "dispatch_id": result.dispatch_id,
        "flight_units_executed": result.flight_units_executed,
        "collisions_detected": list(result.collisions_detected),
        "successful_missions": list(result.successful_missions),
        "failed_missions": list(result.failed_missions),
        "verdict": result.verdict,
        "receipt_digest": result.receipt_digest,
        "timestamp": result.timestamp,
    }

    evidence_path = Path("evidence_capture/fleet_concurrency_evidence.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence_data, indent=2), encoding="utf-8")
    print(f"[✓] Fleet Concurrency Engine Evidence generated at {evidence_path}")

if __name__ == "__main__":
    main()
