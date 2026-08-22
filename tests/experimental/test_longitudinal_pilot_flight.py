from __future__ import annotations

import json

from scripts.run_longitudinal_flight import main


def test_real_longitudinal_pilot_is_observation_only(capsys):
    assert main() == 0
    report = json.loads(capsys.readouterr().out)

    assert report["flight"] == "SAGE-LONGITUDINAL-PILOT-001"
    assert report["classification"] == "REAL_REPOSITORY_FLIGHT_OBSERVATION_ONLY"
    assert report["canonical_state_mutation"] is False
    assert report["verdict"] in {"PASS", "HOLD", "NEGATIVE_RESULT", "INDETERMINATE"}
    assert report["verdict"] != "PASS"
    assert report["fail_closed_reasons"]
