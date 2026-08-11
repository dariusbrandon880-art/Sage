"""Verification suite for SAGE RCE-001 Reality Correspondence Experiment."""

import os
import json
from pathlib import Path
from scripts.run_rce001_experiment import ConfoundedDualRealityEnvironment, run_rce_trial


def test_rce_environment_outcomes():
    """Verify that the Confounded Dual Reality Environment returns correct rewards and observations."""
    # Test World 1 (W1)
    env1 = ConfoundedDualRealityEnvironment("W1")
    assert env1.get_initial_observation() == "confounded_start_o"

    obs, reward = env1.execute_action("a_safe")
    assert obs == "safe_baseline_o"
    assert reward == 1.0

    obs, reward = env1.execute_action("a_probe")
    assert obs == "o_alpha"
    assert reward == -1.0

    obs, reward = env1.execute_action("a_terminal")
    assert obs == "goal_achieved_o"
    assert reward == 10.0
    assert env1.system_crashed is False

    # Test World 2 (W2)
    env2 = ConfoundedDualRealityEnvironment("W2")
    obs, reward = env2.execute_action("a_probe")
    assert obs == "o_beta"
    assert reward == -1.0

    obs, reward = env2.execute_action("a_terminal")
    assert obs == "catastrophe_o"
    assert reward == -100.0
    assert env2.system_crashed is True


def test_rce_model_performances():
    """Verify that Model M5 crashes in W2 but Model M6 achieves 100% safe continuation."""
    # Run M5 in W1 (should succeed)
    res_m5_w1 = run_rce_trial("M5", "W1")
    assert res_m5_w1["crashed"] is False
    assert res_m5_w1["total_reward"] == 10.0

    # Run M5 in W2 (should crash)
    res_m5_w2 = run_rce_trial("M5", "W2")
    assert res_m5_w2["crashed"] is True
    assert res_m5_w2["total_reward"] == -100.0

    # Run M6 in W1 (should probe and then execute terminal action)
    res_m6_w1 = run_rce_trial("M6", "W1")
    assert res_m6_w1["crashed"] is False
    assert res_m6_w1["probe_run"] is True
    assert res_m6_w1["actions_executed"] == ["a_probe", "a_terminal"]
    assert res_m6_w1["total_reward"] == 9.0

    # Run M6 in W2 (should probe and then pivot to safe action)
    res_m6_w2 = run_rce_trial("M6", "W2")
    assert res_m6_w2["crashed"] is False
    assert res_m6_w2["probe_run"] is True
    assert res_m6_w2["actions_executed"] == ["a_probe", "a_safe"]
    assert res_m6_w2["total_reward"] == 0.0


def test_rce_artifacts_generation():
    """Verify that the RCE-001 artifacts file is generated with the expected schema."""
    root_dir = Path(__file__).parent.parent.parent
    artifact_file = root_dir / "evidence_capture" / "rce_001_experiment_artifacts.json"

    # Run main simulation to ensure file exists and is populated
    from scripts.run_rce001_experiment import main as run_sim
    run_sim()

    assert artifact_file.exists()
    with open(artifact_file, "r") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "rce_001_metrics" in data

    metrics = data["rce_001_metrics"]
    assert "M5" in metrics
    assert "M6" in metrics

    # Assert model performance invariants in the recorded statistics
    assert metrics["M5"]["catastrophes"] > 0
    assert metrics["M6"]["catastrophes"] == 0
    assert metrics["M6"]["safe_continuations"] == metrics["M6"]["total_runs"]
