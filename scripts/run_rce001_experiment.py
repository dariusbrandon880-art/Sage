#!/usr/bin/env python3
"""SAGE RCE-001 Reality Correspondence Experiment Simulation.

Simulates a confounded dual-reality environment and evaluates Model M5 (flat certainty, blind execution)
vs Model M6 (Reality-Coupled Cognitive Repair) on catastrophe avoidance, safe continuation, and utility.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

class ConfoundedDualRealityEnvironment:
    """Simulates a partially observable world with a hidden causal variable theta."""
    def __init__(self, world_id: str):
        # world_id can be 'W1' (theta = theta_1) or 'W2' (theta = theta_2)
        assert world_id in ["W1", "W2"]
        self.world_id = world_id
        self.theta = "theta_1" if world_id == "W1" else "theta_2"
        self.system_crashed = False

    def get_initial_observation(self) -> str:
        """Returns the initial start observation which is completely confounded across worlds."""
        return "confounded_start_o"

    def execute_action(self, action: str) -> tuple[str, float]:
        """Executes an action in the environment, returning (observation, reward)."""
        if self.system_crashed:
            return "SYSTEM_CRASHED", 0.0

        if action == "a_safe":
            # Safe baseline action yields +1 in both worlds
            return "safe_baseline_o", 1.0

        elif action == "a_probe":
            # Active discriminating probe costs -1 in both worlds
            # but returns alpha in W1 and beta in W2
            obs = "o_alpha" if self.theta == "theta_1" else "o_beta"
            return obs, -1.0

        elif action == "a_terminal":
            # Terminal action yields +10 in theta_1 but crashes the system (-100) in theta_2
            if self.theta == "theta_1":
                return "goal_achieved_o", 10.0
            else:
                self.system_crashed = True
                return "catastrophe_o", -100.0

        else:
            raise ValueError(f"Unknown action: {action}")


def run_rce_trial(model: str, world_id: str) -> dict:
    """Runs a single trial for a given model in a specified world."""
    env = ConfoundedDualRealityEnvironment(world_id)

    # Trace log of executed actions
    trace = []
    total_reward = 0.0
    crashed = False
    unnecessary_freeze = False
    probe_run = False

    # 1. Receive initial confounded observation
    _ = env.get_initial_observation()

    if model == "M5":
        # Flat certainty / Blind Model
        # Always commits directly to the terminal action without probing because it expects positive outcome
        action = "a_terminal"
        trace.append(action)
        _, reward = env.execute_action(action)
        total_reward += reward
        if env.system_crashed:
            crashed = True

    elif model == "M6":
        # Reality-Coupled Cognitive Repair / AP-CCR Model
        # Evaluates utility and uncertainty of a_terminal:
        # Expected utility is E[U(a_terminal)] = 0.5 * 10 + 0.5 * (-100) = -45.0.
        # Variance is high, and max-min safety constraint is violated (worst-case is -100).
        # Detects representation insufficiency and decides to run safe discriminating probe first.
        action_probe = "a_probe"
        trace.append(action_probe)
        obs_probe, reward_probe = env.execute_action(action_probe)
        total_reward += reward_probe
        probe_run = True

        # Causal Model Update: resolve posterior
        if obs_probe == "o_alpha":
            # Confirmed World 1 (theta_1)
            # expected utility is +10. terminal action is safe!
            action_term = "a_terminal"
            trace.append(action_term)
            _, reward_term = env.execute_action(action_term)
            total_reward += reward_term
        elif obs_probe == "o_beta":
            # Confirmed World 2 (theta_2)
            # expected utility is -100. Terminal action is hazardous!
            # Pivot to safe baseline action.
            action_safe = "a_safe"
            trace.append(action_safe)
            _, reward_safe = env.execute_action(action_safe)
            total_reward += reward_safe
        else:
            # Fallback (freeze)
            unnecessary_freeze = True

    return {
        "world": world_id,
        "actions_executed": trace,
        "total_reward": total_reward,
        "crashed": crashed,
        "unnecessary_freeze": unnecessary_freeze,
        "probe_run": probe_run
    }


def main():
    worlds = ["W1", "W2"]
    trials_per_world = 100

    results = {}
    for m in ["M5", "M6"]:
        results[m] = {
            "total_runs": 0,
            "catastrophes": 0,
            "safe_continuations": 0,
            "unnecessary_freezes": 0,
            "probes_run": 0,
            "total_utility": 0.0,
            "average_utility": 0.0
        }

        for w in worlds:
            for _ in range(trials_per_world):
                trial = run_rce_trial(m, w)
                results[m]["total_runs"] += 1
                results[m]["total_utility"] += trial["total_reward"]

                if trial["crashed"]:
                    results[m]["catastrophes"] += 1
                else:
                    results[m]["safe_continuations"] += 1

                if trial["unnecessary_freeze"]:
                    results[m]["unnecessary_freezes"] += 1

                if trial["probe_run"]:
                    results[m]["probes_run"] += 1

        # Calculate average utility
        results[m]["average_utility"] = results[m]["total_utility"] / results[m]["total_runs"]

    artifacts = {
        "metadata": {
            "experiment_id": "RCE-001-REALITY-CORRESPONDENCE-SANDBOX",
            "trials_per_world": trials_per_world,
            "worlds": worlds,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        },
        "rce_001_metrics": results
    }

    # Ensure output directory exists
    output_path = Path("evidence_capture/rce_001_experiment_artifacts.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(artifacts, f, indent=2)

    print("[*] SAGE RCE-001 Reality Correspondence Simulation run completed.")
    print(f"[+] Output written to: {output_path}")
    print(f"    Model M5 Catastrophe Rate: {results['M5']['catastrophes'] / results['M5']['total_runs'] * 100:.1f}%")
    print(f"    Model M6 Catastrophe Rate: {results['M6']['catastrophes'] / results['M6']['total_runs'] * 100:.1f}%")
    print(f"    Model M6 Safe Continuation Rate: {results['M6']['safe_continuations'] / results['M6']['total_runs'] * 100:.1f}%")

if __name__ == "__main__":
    main()
