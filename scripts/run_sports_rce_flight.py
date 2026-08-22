#!/usr/bin/env python3
"""Execute a SAGE Sports/RCE research-only observation flight."""

import datetime as dt
import json
import sys
from sage.experimental.sports_rce import SportsRCEResearchEngine


def main():
    engine = SportsRCEResearchEngine()
    flight_num = sys.argv[1] if len(sys.argv) > 1 else "2"
    filename = f"sports_real_flight_{int(flight_num):03d}.json"
    exclude = {"2398016"} if flight_num == "2" else set()
    observation_date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    event = engine.fetch_upcoming_event(date_str=observation_date, exclude_event_ids=exclude)
    selection = event.get("strHomeTeam")
    predicted_prob = 0.545 if flight_num == "2" else 0.585
    record = engine.create_pre_game_prediction(
        event_raw=event,
        selection=selection,
        predicted_probability=predicted_prob,
        reasoning="Research-only structural observation; temporal lock precedes event start.",
    )
    artifact_path = engine.persist_prediction_artifact(record, filename=filename)
    print(json.dumps({"flight": flight_num, "observation_date": observation_date, "artifact": str(artifact_path), "record": record}, indent=2, default=str))


if __name__ == "__main__":
    main()
