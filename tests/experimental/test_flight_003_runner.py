import json
import os
import subprocess
import sys
from pathlib import Path


def test_flight_003_runner_emits_observation_only_record() -> None:
    script = Path(__file__).parents[2] / "scripts" / "run_longitudinal_flight_003.py"
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).parents[2])}
    result = subprocess.run([sys.executable, str(script)], check=False, capture_output=True, text=True, env=env)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["flight"] == "003"
    assert payload["observation_only"] is True
    assert payload["verdict"] == "OBSERVATION_RECORDED"
    assert payload["report"]["observed_long_horizon_residual"] == 0.5
