"""SAGE ACR-X Proofreader Engine.

Provides mathematical formulations for Shannon Entropy, Variational Free Energy,
Identity Drift Index (IDI), Memory Stability Score (MSS), and Recovery Fidelity (RF)
using pure Python standard library only.
"""

import math
from typing import Any


class ACRXProofreader:
    """Mathematical metrics and evaluations engine for SAGE ACR-X."""

    @staticmethod
    def calculate_shannon_entropy(data: str) -> float:
        """Calculates Shannon entropy on a string character distribution."""
        if not data:
            return 0.0

        total_len = len(data)
        freqs: dict[str, int] = {}
        for char in data:
            freqs[char] = freqs.get(char, 0) + 1

        entropy = 0.0
        for count in freqs.values():
            p = count / total_len
            entropy -= p * math.log2(p)

        return round(entropy, 4)

    @staticmethod
    def calculate_identity_drift(observed: dict[str, Any], baseline: dict[str, Any]) -> float:
        """Calculates Identity Drift Index (IDI) = || observed - baseline || / || baseline ||.

        State vectors are mapped from dictionary numerical indicators:
        - objective_weight: 1.0 if exists else 0.0
        - task_weight: 1.0 if exists else 0.0
        - blockers_count: integer
        - dependencies_count: integer
        - memory_objects_count: integer
        - decisions_count: integer
        """

        def extract_vector(state: dict[str, Any]) -> list[float]:
            obj_w = 1.0 if state.get("current_objective") else 0.0
            task_w = 1.0 if state.get("active_task") else 0.0
            blockers = len(state.get("blockers", []))
            dependencies = len(state.get("dependencies", []))
            memories = state.get("memory_count", 0) or len(state.get("memories", []))
            decisions = state.get("decision_count", 0) or len(state.get("decisions", []))
            return [
                float(obj_w),
                float(task_w),
                float(blockers),
                float(dependencies),
                float(memories),
                float(decisions),
            ]

        obs_v = extract_vector(observed)
        base_v = extract_vector(baseline)

        # Vector difference magnitude
        diff_sq_sum = sum((o - b) ** 2 for o, b in zip(obs_v, base_v))
        diff_norm = math.sqrt(diff_sq_sum)

        # Baseline vector magnitude
        base_sq_sum = sum(b**2 for b in base_v)
        base_norm = math.sqrt(base_sq_sum)

        if base_norm == 0.0:
            return 0.0 if diff_norm == 0.0 else 1.0

        return round(diff_norm / base_norm, 4)

    @staticmethod
    def calculate_variational_free_energy(
        observed: dict[str, Any], baseline: dict[str, Any], entropy_input: str
    ) -> float:
        """Calculates Variational Free Energy: discrepancy of drift * log(1+drift) + entropy."""
        idi = ACRXProofreader.calculate_identity_drift(observed, baseline)
        entropy = ACRXProofreader.calculate_shannon_entropy(entropy_input)

        # Complexity - Accuracy abstraction
        # If IDI drift is high, discrepancy complexity increases variational free energy
        vfe = idi * math.log(1.0 + idi) + entropy
        return round(vfe, 4)

    @staticmethod
    def calculate_memory_stability(
        retained_validated_count: int, transient_influx_count: int
    ) -> float:
        """Calculates Memory Stability Score (MSS) = validated retained knowledge / transient memory influx."""
        if transient_influx_count == 0:
            return float(retained_validated_count)

        mss = retained_validated_count / transient_influx_count
        return round(mss, 4)

    @staticmethod
    def calculate_recovery_fidelity(pre_state: dict[str, Any], post_state: dict[str, Any]) -> float:
        """Calculates Recovery Fidelity (RF) measuring restoration accuracy (0.0 to 1.0)."""
        keys = ["current_objective", "active_task", "blockers", "dependencies"]
        matches = 0
        total = len(keys)

        for k in keys:
            pre_val = pre_state.get(k)
            post_val = post_state.get(k)
            if k in ["blockers", "dependencies"]:
                # Jaccard matching
                pre_set = set(pre_val or [])
                post_set = set(post_val or [])
                if not pre_set and not post_set:
                    matches += 1
                elif pre_set and post_set:
                    intersect = pre_set.intersection(post_set)
                    union = pre_set.union(post_set)
                    matches += len(intersect) / len(union)
            else:
                if pre_val == post_val:
                    matches += 1

        return round(matches / total, 4)
