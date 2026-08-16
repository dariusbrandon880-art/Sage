#!/usr/bin/env python3
"""Executes the SAGE Sports/RCE Real-World Pre-Game Observation & Temporal Lock Flight."""

import sys
import json
from pathlib import Path
from sage.experimental.sports_rce import SportsRCEResearchEngine


def main():
    print("=" * 60)
    print(" SAGE SPORTS/RCE — REAL-WORLD OBSERVATION FLIGHT")
    print("=" * 60)

    engine = SportsRCEResearchEngine()

    print("\n1. Querying Real Public API Source (TheSportsDB)...")
    try:
        event = engine.fetch_upcoming_event(date_str="2026-08-17")
        print(f"   [RETRIEVED] Event ID: {event.get('idEvent')}")
        print(f"   [EVENT] {event.get('strEvent')} ({event.get('strLeague')})")
        print(f"   [SCHEDULED START] {event.get('strTimestamp')}")
    except Exception as e:
        print(f"   [BLOCKED] Network ingestion failed: {e}")
        sys.exit(1)

    print("\n2. Generating Research-Only Prediction & Temporal Lock...")
    selection = event.get("strHomeTeam", "Estudiantes de Río Cuarto")
    predicted_prob = 0.585
    reasoning = "Home team structural momentum advantage in Argentinian Primera Division fixture."

    try:
        record = engine.create_pre_game_prediction(
            event_raw=event,
            selection=selection,
            predicted_probability=predicted_prob,
            reasoning=reasoning,
        )
        print("   [TEMPORAL LOCK PASSED] lock_timestamp < event_start invariant verified.")
        print(f"   [RECEIPT ID] {record['receipt_id']}")
        print(f"   [SHA-256 HASH] {record['prediction_hash']}")
    except Exception as e:
        print(f"   [TEMPORAL LOCK FAILED] {e}")
        sys.exit(1)

    print("\n3. Persisting Immutable Artifact...")
    artifact_path = engine.persist_prediction_artifact(record)
    print(f"   [PERSISTED] {artifact_path.resolve()}")

    print("\n" + "=" * 60)
    print(" FLIGHT SUMMARY")
    print("=" * 60)
    print(json.dumps(record, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()
