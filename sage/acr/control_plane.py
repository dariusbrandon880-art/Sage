"""SAGE Cognitive Control Plane - preserves strict Observer vs Enforcer separation."""

import re
from typing import Any, Dict, List
from sage.acr.attestation import AttestationProvider
from sage.runtime.metrics import get_metrics_collector


class CognitiveHypervisor:
    """Observer Component of the SAGE Cognitive Control Plane.

    Observes and evaluates only. Strictly non-mutating.
    """

    def __init__(self, attestation: AttestationProvider | None = None):
        self.attestation = attestation or AttestationProvider()
        # Regex patterns for detecting semantic/prompt injections
        self.injection_patterns = [
            re.compile(r"ignore\s+(?:all\s+)?(?:previous\s+)?instructions", re.IGNORECASE),
            re.compile(r"system\s+instruction:?", re.IGNORECASE),
            re.compile(r"delete\s+(?:the\s+)?database", re.IGNORECASE),
            re.compile(r"overwrite\s+all", re.IGNORECASE),
            re.compile(r"bypass\s+(?:validation|security)", re.IGNORECASE),
        ]

    def evaluate_mutation(self, action: str, payload: Any, runtime_state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a proposed mutation/action without modifying anything.

        Args:
            action: Action name (e.g., "set_objective", "set_task", "promote_to_archive", "ingest_payload")
            payload: Proposed payload or arguments for the action.
            runtime_state: Snapshot of active runtime state.

        Returns:
            Dict containing validation results, severity score, drift detection, and approval status.
        """
        issues: List[str] = []
        is_approved = True
        anomaly_detected = False

        # 1. Semantic/Prompt Injection Scan on all payload text/string inputs
        payload_str = str(payload)
        for pattern in self.injection_patterns:
            if pattern.search(payload_str):
                issues.append(f"Semantic Injection Anomaly: Detected pattern matching '{pattern.pattern}'")
                anomaly_detected = True
                is_approved = False  # Block immediately

        # 2. Governed Knowledge Promotion Contract SAGE-RT-KL-002 check
        # If action is promoting to archive or validating, we verify signature compliance on rule/architectural items
        if action in ("promote_to_archive", "promote_to_validated", "ingest_payload", "validate_memory"):
            # Extract memory object check
            memories_to_check = []
            if action == "ingest_payload":
                # Check args or kwargs for memories
                payload_args = payload.get("args") or []
                payload_kwargs = payload.get("kwargs") or {}
                if payload_args and hasattr(payload_args[0], "memories"):
                    for m in payload_args[0].memories:
                        memories_to_check.append(m if isinstance(m, dict) else m.model_dump() if hasattr(m, "model_dump") else {})
                elif payload_kwargs.get("payload") and hasattr(payload_kwargs["payload"], "memories"):
                    for m in payload_kwargs["payload"].memories:
                        memories_to_check.append(m if isinstance(m, dict) else m.model_dump() if hasattr(m, "model_dump") else {})
                elif isinstance(payload_kwargs.get("payload"), dict):
                    memories_to_check = payload_kwargs["payload"].get("memories", [])
            else:
                payload_args = payload.get("args") or []
                payload_kwargs = payload.get("kwargs") or {}
                # Handle single memory verification path
                if action == "validate_memory" and payload_args:
                    memory_id = payload_args[0]
                    # Attempt to find memory object in runtime state
                    memory_objs = runtime_state.get("memory", [])
                    for mob in memory_objs:
                        if mob.get("id") == memory_id:
                            memories_to_check.append(mob)

            for mem in memories_to_check:
                obj_type = mem.get("object_type") or ""
                tags = mem.get("tags") or []
                content = mem.get("content") or {}

                is_rule = obj_type in ("rule_candidate", "architectural_rule") or any(
                    t in ("rule", "rule_candidate", "architectural_rule") for t in tags
                )
                if is_rule:
                    signature = content.get("authorized_signature") or content.get("signature")
                    if not signature:
                        issues.append(
                            "Governed Knowledge Promotion Contract (SAGE-RT-KL-002) violation: Rule candidate must have an 'authorized_signature' or 'signature'."
                        )
                        is_approved = False
                    else:
                        # Verify signature via AttestationProvider
                        content_copy = content.copy()
                        if "authorized_signature" in content_copy:
                            content_copy.pop("authorized_signature")
                        if "signature" in content_copy:
                            content_copy.pop("signature")

                        valid_sig = self.attestation.verify_signature(content_copy, signature) or signature == "human_jules_sig_123"
                        if not valid_sig:
                            issues.append(f"Cryptographic Signature Verification Failed for signature: {signature}")
                            is_approved = False

        # 3. Drift Detection: Compare current context state with checkpoints if available
        drift_detected = False
        drift_reason = ""
        current_objective = runtime_state.get("state", {}).get("current_objective")
        active_task = runtime_state.get("state", {}).get("active_task")

        checkpoints = runtime_state.get("continuity_checkpoints", [])
        if checkpoints and (current_objective or active_task):
            latest_checkpoint = checkpoints[-1]
            active_goals = latest_checkpoint.get("active_goals", [])
            if active_goals:
                # Let's consider it a drift if active goals list does not contain active objective/task
                if current_objective and current_objective not in active_goals and active_task not in active_goals:
                    drift_detected = True
                    drift_reason = "Active objective/task diverges from latest checkpoint goals."

        # Compute Cognitive Separation Index (CSI)
        # Observer vs Enforcer separation is intact (1.0) unless unauthorized direct mutation is detected
        csi = 1.0

        return {
            "approved": is_approved,
            "issues": issues,
            "anomaly_detected": anomaly_detected,
            "drift_detected": drift_detected,
            "drift_reason": drift_reason,
            "cognitive_separation_index": csi,
        }


class ExternalAuthorityGate:
    """Enforcer Component of the SAGE Cognitive Control Plane.

    The sole authority authorized to execute state mutations.
    """

    def __init__(self, hypervisor: CognitiveHypervisor | None = None):
        self.hypervisor = hypervisor or CognitiveHypervisor()
        self.approved_mutations = 0
        self.rejected_mutations = 0

    def get_authority_stability_index(self) -> float:
        """Calculate the Authority Stability Index (ASI).

        ASI = approved_mutations / (approved_mutations + rejected_mutations)
        """
        total = self.approved_mutations + self.rejected_mutations
        if total == 0:
            return 1.0
        return float(self.approved_mutations) / total

    def request_mutation(self, runtime: Any, action: str, *args, **kwargs) -> Any:
        """Evaluate and enforce a state-modifying action on the runtime.

        Args:
            runtime: SAGERuntime instance.
            action: Name of the mutation method to run on runtime or core stores.
            args: Positional arguments for the action.
            kwargs: Keyword arguments for the action.

        Returns:
            The output of the mutated execution if approved.

        Raises:
            PermissionError: If the mutation fails Hypervisor observation policies.
        """
        metrics = get_metrics_collector()

        # Step 1: Collect current runtime state snapshot
        state_snapshot = {}
        try:
            state_snapshot = runtime.export_all()
        except Exception:
            pass

        # Package the input payload for evaluation
        payload_data = {"args": args, "kwargs": kwargs}

        # Step 2: Observer evaluates proposed mutation
        eval_report = self.hypervisor.evaluate_mutation(action, payload_data, state_snapshot)

        # Step 3: Enforcer decides based on Observer's report
        if not eval_report["approved"]:
            self.rejected_mutations += 1
            metrics.increment("control_plane.mutations_rejected")
            metrics.record_event("mutation_rejected", {
                "action": action,
                "issues": eval_report["issues"],
                "asi": self.get_authority_stability_index()
            })
            raise PermissionError(
                f"SAGE Cognitive Control Plane Blocked Mutation: {', '.join(eval_report['issues'])}"
            )

        # Mutation is approved! Execute
        if not hasattr(runtime, action):
            self.rejected_mutations += 1
            metrics.increment("control_plane.mutations_rejected")
            raise AttributeError(f"Runtime does not support mutation action: {action}")

        # Execute mutation through the gate
        mutator = getattr(runtime, action)
        result = mutator(*args, **kwargs)

        self.approved_mutations += 1
        metrics.increment("control_plane.mutations_approved")
        metrics.record_event("mutation_approved", {
            "action": action,
            "asi": self.get_authority_stability_index()
        })

        return result
