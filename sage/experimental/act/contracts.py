"""SAGE Agent Continuity Tree Read-Only Interface Contracts."""

import re
from typing import Any, Dict, List
from datetime import datetime, timezone


class SessionTaskTreeLinker:
    """Enforces read-only schema mapping and validation for Session-to-Task lineage.

    Under Milestone 1 rules, this class operates strictly in a read-only, non-mutating
    fashion, verifying structures and generating mapping lineage models.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize linker contract."""
        self.validation_mode = validation_mode

    def link_session_to_tasks(self, session_id: str, task_ids: List[str]) -> Dict[str, Any]:
        """Perform schema validation and return a read-only mapped session-to-task tree.

        Args:
            session_id: The target session identifier.
            task_ids: A list of task identifiers to map.

        Returns:
            A dictionary representing the verified mapped lineage tree.

        Raises:
            ValueError: If session_id or task_ids fail structural format checks.
        """
        if not session_id or not session_id.startswith("session_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid session_id format: '{session_id}'")

        for task_id in task_ids:
            if not task_id or not task_id.startswith("task_"):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{task_id}'")

        # Map and return the structured lineage without writing or mutating system files
        return {
            "session_id": session_id,
            "mapped_tasks": list(task_ids),
            "linked_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "INTERFACE_VERIFIED",
            "read_only_assertion": True,
        }


class CapabilityPassportValidator:
    """Enforces programmatic, read-only validation of Capability Passport documents.

    Strictly enforces the 'No Orphan Capability' policy by ensuring every
    operational component maps to an authorized, documented, and reviewed passport.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize passport validator."""
        self.validation_mode = validation_mode

    def validate_passport(self, passport: Dict[str, Any]) -> Dict[str, Any]:
        """Validates a capability passport document structure against standard rules.

        Args:
            passport: The dictionary representing the capability passport.

        Returns:
            A metadata dictionary containing the validation outcome.

        Raises:
            ValueError: If required fields are missing, invalid formats are detected,
                        or No Orphan constraints are violated.
        """
        if not isinstance(passport, dict):
            raise ValueError("Passport Violation: Passport must be a dictionary.")

        # 1. Required field verification
        required_fields = [
            "capability_id",
            "name",
            "purpose",
            "lifecycle_state",
            "validation_strategy",
            "evidence_path",
            "dependencies",
            "human_signoff",
        ]
        for field in required_fields:
            if field not in passport:
                raise ValueError(f"Passport Violation: Missing required field '{field}'.")

        # 2. Field Type validation
        # strings
        for field in ["capability_id", "name", "purpose", "validation_strategy"]:
            if not isinstance(passport[field], str) or not passport[field].strip():
                raise ValueError(f"Passport Violation: '{field}' must be a non-empty string.")

        # capability_id pattern verification
        cap_id = passport["capability_id"]
        if not re.match(r"^cap_[a-zA-Z0-9_]{3,64}$", cap_id):
            raise ValueError(f"Passport Violation: Invalid capability_id format: '{cap_id}'")

        # 3. Lifecycle State Validation
        allowed_states = ["proposed", "validated", "archive_candidate", "canonical"]
        state = str(passport["lifecycle_state"]).lower()
        if state not in allowed_states:
            raise ValueError(f"Passport Violation: Invalid lifecycle_state: '{state}'. Allowed states: {allowed_states}")

        # 4. Evidence Path presence and validation
        ev_path = passport["evidence_path"]
        if not isinstance(ev_path, str) or not ev_path.strip():
            raise ValueError("Passport Violation: 'evidence_path' must be a non-empty string.")
        if not ev_path.startswith("docs/") and not ev_path.startswith("evidence/"):
            raise ValueError(f"Passport Violation: 'evidence_path' must point to docs/ or evidence/, got: '{ev_path}'")

        # 5. Dependency declaration verification
        deps = passport["dependencies"]
        if not isinstance(deps, list):
            raise ValueError("Passport Violation: 'dependencies' must be a list of strings.")
        for dep in deps:
            if not isinstance(dep, str) or not re.match(r"^cap_[a-zA-Z0-9_]{3,64}$", dep):
                raise ValueError(f"Passport Violation: Invalid dependency identifier: '{dep}'")

        # 6. Human Signoff presence and verification
        signoff = passport["human_signoff"]
        if not isinstance(signoff, dict):
            raise ValueError("Passport Violation: 'human_signoff' must be a dictionary.")
        required_signoff = ["signer", "timestamp", "approved"]
        for field in required_signoff:
            if field not in signoff:
                raise ValueError(f"Passport Violation: Missing required field 'human_signoff.{field}'.")
        if not isinstance(signoff["approved"], bool):
            raise ValueError("Passport Violation: 'human_signoff.approved' must be a boolean.")

        # Monotonicity check: If approved is False, reject validated/canonical states
        if not signoff["approved"] and state in ["validated", "canonical"]:
            raise ValueError(f"Passport Violation: Unauthorized transition. State cannot be '{state}' without active human approval.")

        # Complete and return verification result
        return {
            "capability_id": cap_id,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "PASSPORT_VALIDATED",
            "approved": signoff["approved"],
            "read_only_assertion": True,
        }


class CapabilityEvidenceReceiptGenerator:
    """Generates secure, structured Evidence Receipts to track SAGE capability passport validation events.

    Implements read-only artifact creation adhering strictly to SAGE's Evidence Lifecycle
    and parallel validation frameworks.
    """

    def __init__(self, validator_id: str = "val_system_v1"):
        """Initialize receipt generator."""
        self.validator_id = validator_id

    def generate_receipt(
        self,
        passport: Dict[str, Any],
        validation_result: Dict[str, Any],
        receipt_id: str | None = None,
    ) -> Dict[str, Any]:
        """Creates a signed capability evidence receipt.

        Args:
            passport: The dictionary representing the validated Capability Passport.
            validation_result: Output from CapabilityPassportValidator.
            receipt_id: Optional unique identifier. If not provided, a secure hash is generated.

        Returns:
            A dictionary conforming to SAGE's Capability Evidence Receipt Schema.

        Raises:
            ValueError: If either dictionary is malformed or required attributes are invalid.
        """
        # 1. Structural verification of input contracts
        if not isinstance(passport, dict) or "capability_id" not in passport:
            raise ValueError("Receipt Violation: Invalid or incomplete passport dictionary.")
        if not isinstance(validation_result, dict) or "validation_status" not in validation_result:
            raise ValueError("Receipt Violation: Invalid or incomplete validation_result dictionary.")

        # Ensure validation state matches passport capability identifier
        capability_id = passport["capability_id"]
        if validation_result.get("capability_id") != capability_id:
            raise ValueError("Receipt Violation: Capability ID mismatch between passport and validation_result.")

        # 2. Determine identifiers
        import hashlib
        import uuid
        if not receipt_id:
            raw_hash_data = f"{capability_id}:{validation_result.get('validated_at')}:{self.validator_id}"
            secure_hash = hashlib.sha256(raw_hash_data.encode()).hexdigest()[:16]
            receipt_id = f"rcpt_{secure_hash}"

        if not re.match(r"^rcpt_[a-zA-Z0-9_]{8,64}$", receipt_id):
            raise ValueError(f"Receipt Violation: Invalid format for receipt_id: '{receipt_id}'")

        # 3. Core field compilation
        evidence_reference = passport.get("evidence_path", "")
        if not isinstance(evidence_reference, str) or not evidence_reference.strip():
            raise ValueError("Receipt Violation: Missing or invalid 'evidence_reference'.")

        review_status = "approved" if validation_result.get("approved") is True else "pending"
        archive_destination = f"Main Archive/{capability_id}_receipt.json"

        # Construct structured receipt
        receipt = {
            "receipt_id": receipt_id,
            "capability_id": capability_id,
            "validator_id": self.validator_id,
            "validation_result": {
                "status": validation_result["validation_status"],
                "validated_at": validation_result.get("validated_at"),
                "approved": validation_result.get("approved", False)
            },
            "evidence_reference": evidence_reference,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "review_status": review_status,
            "archive_destination": archive_destination,
        }

        # 4. Programmatic constraints checking
        # Verify all 8 fields are structurally populated
        required_receipt_fields = [
            "receipt_id",
            "capability_id",
            "validator_id",
            "validation_result",
            "evidence_reference",
            "timestamp",
            "review_status",
            "archive_destination",
        ]
        for field in required_receipt_fields:
            if field not in receipt or receipt[field] is None:
                raise ValueError(f"Receipt Violation: Missing required receipt field '{field}'.")

        if review_status not in ["approved", "pending", "rejected"]:
            raise ValueError(f"Receipt Violation: Invalid receipt review status: '{review_status}'.")

        # 5. Output read-only outcome with traceability marker
        return {
            "receipt": receipt,
            "traceability_chain_valid": True,
            "read_only_assertion": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


class HumanReviewGate:
    """Enforces the final manual/cognitive gate checkpoint prior to any capability promotion.

    Processes, structures, and validates a Human Review decision based on the
    evaluation of a previously generated Capability Evidence Receipt.
    """

    def __init__(self, reviewer_identity: str = "supervisor_v1"):
        """Initialize human review gate validator."""
        self.reviewer_identity = reviewer_identity

    def execute_review(
        self,
        receipt: Dict[str, Any],
        decision: str,  # "approved" or "rejected"
        notes: str,
        review_id: str | None = None,
    ) -> Dict[str, Any]:
        """Validates a capability evidence receipt and compiles a structured Human Review trace.

        Args:
            receipt: Output dictionary from CapabilityEvidenceReceiptGenerator representing the receipt.
            decision: Explicit string indicating the reviewer choice ("approved" or "rejected").
            notes: Non-empty rationale string.
            review_id: Optional identifier. If not provided, a secure hash ID is generated.

        Returns:
            A dictionary containing the validated Human Review audit trace.

        Raises:
            ValueError: If inputs are invalid, required receipt fields are missing, or notes are empty.
        """
        # 1. Verification of incoming receipt structure
        if not isinstance(receipt, dict):
            raise ValueError("Review Violation: Evidence receipt must be a dictionary.")

        # Extract inner 'receipt' if passed as wrapper, or handle raw receipt dict
        target_receipt = receipt.get("receipt") if "receipt" in receipt else receipt
        if not isinstance(target_receipt, dict):
            raise ValueError("Review Violation: Invalid or incomplete receipt dictionary.")

        # Verify all 8 required evidence fields exist in the receipt
        required_evidence_fields = [
            "receipt_id",
            "capability_id",
            "validator_id",
            "validation_result",
            "evidence_reference",
            "timestamp",
            "review_status",
            "archive_destination",
        ]
        for field in required_evidence_fields:
            if field not in target_receipt:
                raise ValueError(f"Review Violation: Missing required receipt field '{field}'.")

        # 2. Input Parameter Check
        decision_lower = str(decision).lower()
        if decision_lower not in ["approved", "rejected"]:
            raise ValueError(f"Review Violation: Invalid review decision '{decision}'. Allowed: ['approved', 'rejected']")

        if not isinstance(notes, str) or not notes.strip():
            raise ValueError("Review Violation: Review notes must be a non-empty string.")

        # 3. Compile Identifiers and State Variables
        import hashlib
        receipt_id = target_receipt["receipt_id"]
        capability_id = target_receipt["capability_id"]

        if not review_id:
            raw_hash_data = f"{receipt_id}:{decision_lower}:{self.reviewer_identity}"
            secure_hash = hashlib.sha256(raw_hash_data.encode()).hexdigest()[:16]
            review_id = f"rev_{secure_hash}"

        if not re.match(r"^rev_[a-zA-Z0-9_]{8,64}$", review_id):
            raise ValueError(f"Review Violation: Invalid format for review_id: '{review_id}'")

        # Determine target state status based on decision
        validation_status = "VALIDATED" if decision_lower == "approved" else "REJECTED"
        archive_destination = f"Main Archive/{capability_id}_review_gate.json"

        # Construct review schema dictionary
        review_audit = {
            "review_id": review_id,
            "receipt_id": receipt_id,
            "capability_id": capability_id,
            "reviewer_identity": self.reviewer_identity,
            "review_decision": decision_lower,
            "review_notes": notes.strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_status": validation_status,
            "archive_destination": archive_destination,
        }

        # 4. Programmatic audit verification
        required_review_fields = [
            "review_id",
            "receipt_id",
            "capability_id",
            "reviewer_identity",
            "review_decision",
            "review_notes",
            "timestamp",
            "validation_status",
            "archive_destination",
        ]
        for field in required_review_fields:
            if field not in review_audit or review_audit[field] is None:
                raise ValueError(f"Review Violation: Missing required review field '{field}'.")

        # 5. Output read-only outcome with traceability marker
        return {
            "review_audit": review_audit,
            "audit_trail_valid": True,
            "read_only_assertion": True,
            "finalized_at": datetime.now(timezone.utc).isoformat(),
        }


class CrossModelAuditPayloadValidator:
    """Enforces programmatic, read-only validation for the Cross-Model Audit Payload Schema.

    Strictly complies with the SAGE Cross-Model Audit Payload Schema v1.0, checking
    agent and model identity fields, execution state telemetry, hierarchical task
    lineages, chronological invariants, and relational uniqueness constraints.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize the cross-model audit payload validator."""
        self.validation_mode = validation_mode

    def validate_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validates an incoming audit payload against SAGE CMAPS v1.0 rules.

        Args:
            payload: The dictionary representation of the audit payload.

        Returns:
            A metadata dictionary indicating successful validation and status.

        Raises:
            ValueError: If any structural, format, chronological, or relational checks fail.
        """
        if not isinstance(payload, dict):
            raise ValueError("CMAPS Violation: Payload must be a dictionary.")

        # 1. Structural Field Existence Checks
        required_top_level = [
            "audit_id",
            "timestamp",
            "agent_identity",
            "model_provider",
            "execution_state",
            "task_lineage",
            "decision_events",
            "failure_events",
            "recovery_checkpoints",
            "evidence_relationships",
            "attestation",
        ]
        for field in required_top_level:
            if field not in payload:
                raise ValueError(f"CMAPS Violation: Missing required top-level field '{field}'.")

        # 2. Check inner structures and required sub-fields
        # Agent Identity
        agent_id_data = payload["agent_identity"]
        if not isinstance(agent_id_data, dict):
            raise ValueError("CMAPS Violation: 'agent_identity' must be a dictionary.")
        required_agent = ["agent_id", "name", "role", "governance_tier"]
        for field in required_agent:
            if field not in agent_id_data:
                raise ValueError(f"CMAPS Violation: Missing 'agent_identity.{field}'.")

        # Model Provider
        provider_data = payload["model_provider"]
        if not isinstance(provider_data, dict):
            raise ValueError("CMAPS Violation: 'model_provider' must be a dictionary.")
        required_provider = ["provider", "model_name", "temperature"]
        for field in required_provider:
            if field not in provider_data:
                raise ValueError(f"CMAPS Violation: Missing 'model_provider.{field}'.")

        # Provider-to-model prefix consistency checking
        prov = str(provider_data["provider"]).lower()
        m_name = str(provider_data["model_name"]).lower()
        if prov == "openai" and not ("gpt" in m_name or "o1" in m_name or "o3" in m_name):
            raise ValueError(f"CMAPS Violation: Model/Provider consistency mismatch. Provider '{prov}' cannot run model '{m_name}'.")
        elif prov == "anthropic" and "claude" not in m_name:
            raise ValueError(f"CMAPS Violation: Model/Provider consistency mismatch. Provider '{prov}' cannot run model '{m_name}'.")
        elif prov == "google" and "gemini" not in m_name:
            raise ValueError(f"CMAPS Violation: Model/Provider consistency mismatch. Provider '{prov}' cannot run model '{m_name}'.")

        # Execution State
        exec_state = payload["execution_state"]
        if not isinstance(exec_state, dict):
            raise ValueError("CMAPS Violation: 'execution_state' must be a dictionary.")
        required_exec = ["run_id", "status", "step_counter", "started_at", "updated_at"]
        for field in required_exec:
            if field not in exec_state:
                raise ValueError(f"CMAPS Violation: Missing 'execution_state.{field}'.")

        # Task Lineage
        task_lineage = payload["task_lineage"]
        if not isinstance(task_lineage, dict):
            raise ValueError("CMAPS Violation: 'task_lineage' must be a dictionary.")
        required_lineage = ["session_id", "current_task_id", "subtask_ids"]
        for field in required_lineage:
            if field not in task_lineage:
                raise ValueError(f"CMAPS Violation: Missing 'task_lineage.{field}'.")

        # Attestation
        attestation = payload["attestation"]
        if not isinstance(attestation, dict):
            raise ValueError("CMAPS Violation: 'attestation' must be a dictionary.")
        required_attestation = ["nonce", "signature", "signer_identity"]
        for field in required_attestation:
            if field not in attestation:
                raise ValueError(f"CMAPS Violation: Missing 'attestation.{field}'.")

        # 3. Format and Pattern Verification
        # audit_id: ^audit_[a-fA-F0-9]{32}$
        if not re.match(r"^audit_[a-fA-F0-9]{32}$", payload["audit_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'audit_id': '{payload['audit_id']}'")

        # agent_identity.agent_id: ^agent_[a-zA-Z0-9_]{3,64}$
        if not re.match(r"^agent_[a-zA-Z0-9_]{3,64}$", agent_id_data["agent_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'agent_id': '{agent_id_data['agent_id']}'")

        # execution_state.run_id: ^run_[a-zA-Z0-9]{20,40}$
        if not re.match(r"^run_[a-zA-Z0-9]{20,40}$", exec_state["run_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'run_id': '{exec_state['run_id']}'")

        # task_lineage.session_id: ^session_[a-fA-F0-9]{8}$
        if not re.match(r"^session_[a-fA-F0-9]{8}$", task_lineage["session_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'session_id': '{task_lineage['session_id']}'")

        # task_lineage.current_task_id: ^task_[a-zA-Z0-9_]{3,128}$
        if not re.match(r"^task_[a-zA-Z0-9_]{3,128}$", task_lineage["current_task_id"]):
            raise ValueError(f"CMAPS Violation: Invalid format for 'current_task_id': '{task_lineage['current_task_id']}'")

        # task_lineage.parent_task_id: ^task_[a-zA-Z0-9_]{3,128}$ (if present)
        if "parent_task_id" in task_lineage and task_lineage["parent_task_id"] is not None:
            if not re.match(r"^task_[a-zA-Z0-9_]{3,128}$", task_lineage["parent_task_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'parent_task_id': '{task_lineage['parent_task_id']}'")
            if task_lineage["parent_task_id"] == task_lineage["current_task_id"]:
                raise ValueError(f"CMAPS Violation: Task hierarchy violation. parent_task_id cannot equal current_task_id.")

        # List fields checks
        if not isinstance(payload["decision_events"], list):
            raise ValueError("CMAPS Violation: 'decision_events' must be a list.")
        for dec in payload["decision_events"]:
            if not isinstance(dec, dict):
                raise ValueError("CMAPS Violation: Decision entry must be a dictionary.")
            for f in ["decision_id", "timestamp", "summary", "reasoning", "confidence"]:
                if f not in dec:
                    raise ValueError(f"CMAPS Violation: Decision missing required field '{f}'.")
            if not re.match(r"^(decision|proposal)_[a-zA-Z0-9_]{3,128}$", dec["decision_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'decision_id': '{dec['decision_id']}'")

        if not isinstance(payload["failure_events"], list):
            raise ValueError("CMAPS Violation: 'failure_events' must be a list.")
        for fail in payload["failure_events"]:
            if not isinstance(fail, dict):
                raise ValueError("CMAPS Violation: Failure entry must be a dictionary.")
            for f in ["failure_id", "timestamp", "error_type", "message", "severity"]:
                if f not in fail:
                    raise ValueError(f"CMAPS Violation: Failure missing required field '{f}'.")
            if not re.match(r"^fail_[a-zA-Z0-9_]{3,128}$", fail["failure_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'failure_id': '{fail['failure_id']}'")

        if not isinstance(payload["recovery_checkpoints"], list):
            raise ValueError("CMAPS Violation: 'recovery_checkpoints' must be a list.")
        for chk in payload["recovery_checkpoints"]:
            if not isinstance(chk, dict):
                raise ValueError("CMAPS Violation: Checkpoint entry must be a dictionary.")
            for f in ["checkpoint_id", "timestamp", "rehydration_token", "requires_human_approval"]:
                if f not in chk:
                    raise ValueError(f"CMAPS Violation: Checkpoint missing required field '{f}'.")
            if not re.match(r"^chk_[a-zA-Z0-9_]{3,128}$", chk["checkpoint_id"]):
                raise ValueError(f"CMAPS Violation: Invalid format for 'checkpoint_id': '{chk['checkpoint_id']}'")

        # 4. Chronological Invariants Checks
        try:
            started_at = datetime.fromisoformat(exec_state["started_at"].replace("Z", "+00:00"))
            updated_at = datetime.fromisoformat(exec_state["updated_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            raise ValueError(f"CMAPS Violation: Invalid timestamp format in execution_state: {e}")

        # started_at <= updated_at
        if started_at > updated_at:
            raise ValueError(
                f"CMAPS Violation: Chronological mismatch. Run 'started_at' ({started_at}) "
                f"is strictly later than 'updated_at' ({updated_at})."
            )

        # decision timestamps >= started_at and monotonically increasing
        last_dec_time = None
        for dec in payload["decision_events"]:
            try:
                dec_time = datetime.fromisoformat(dec["timestamp"].replace("Z", "+00:00"))
            except (ValueError, TypeError) as e:
                raise ValueError(f"CMAPS Violation: Invalid timestamp format in decision '{dec['decision_id']}': {e}")
            if dec_time < started_at:
                raise ValueError(
                    f"CMAPS Violation: Chronological mismatch. Decision '{dec['decision_id']}' "
                    f"timestamp ({dec_time}) is strictly earlier than run start time ({started_at})."
                )
            if last_dec_time is not None and dec_time < last_dec_time:
                raise ValueError(
                    f"CMAPS Violation: Chronological mismatch. Decision '{dec['decision_id']}' timestamp ({dec_time}) "
                    f"is strictly earlier than previous decision timestamp ({last_dec_time})."
                )
            last_dec_time = dec_time

        # failure timestamps <= checkpoint timestamps
        for fail in payload["failure_events"]:
            try:
                fail_time = datetime.fromisoformat(fail["timestamp"].replace("Z", "+00:00"))
            except (ValueError, TypeError) as e:
                raise ValueError(f"CMAPS Violation: Invalid timestamp format in failure '{fail['failure_id']}': {e}")
            for chk in payload["recovery_checkpoints"]:
                try:
                    chk_time = datetime.fromisoformat(chk["timestamp"].replace("Z", "+00:00"))
                except (ValueError, TypeError) as e:
                    raise ValueError(f"CMAPS Violation: Invalid timestamp format in checkpoint '{chk['checkpoint_id']}': {e}")
                if fail_time > chk_time:
                    raise ValueError(
                        f"CMAPS Violation: Chronological mismatch. Intercepted failure '{fail['failure_id']}' "
                        f"timestamp ({fail_time}) occurred after checkpoint snapshot '{chk['checkpoint_id']}' ({chk_time})."
                    )

        # Evidence relationships validation
        if not isinstance(payload["evidence_relationships"], list):
            raise ValueError("CMAPS Violation: 'evidence_relationships' must be a list.")
        for ev in payload["evidence_relationships"]:
            if not isinstance(ev, dict):
                raise ValueError("CMAPS Violation: Evidence entry must be a dictionary.")
            for f in ["artifact_path", "git_commit", "sha256_checksum"]:
                if f not in ev:
                    raise ValueError(f"CMAPS Violation: Evidence missing required field '{f}'.")
            if not re.match(r"^[a-fA-F0-9]{40}$", ev["git_commit"]):
                raise ValueError(f"CMAPS Violation: Invalid git commit hash format: '{ev['git_commit']}'.")
            if not re.match(r"^[a-fA-F0-9]{64}$", ev["sha256_checksum"]):
                raise ValueError(f"CMAPS Violation: Invalid sha256 checksum format: '{ev['sha256_checksum']}'.")

        # 5. Relational and Multi-Set Uniqueness Constraints
        subtask_ids = task_lineage["subtask_ids"]
        if not isinstance(subtask_ids, list):
            raise ValueError("CMAPS Violation: 'subtask_ids' must be a list of strings.")
        current_task_id = task_lineage["current_task_id"]

        # If recovered state, there must be at least one failure and recovery checkpoint
        if exec_state["status"] == "recovered":
            if not payload["failure_events"]:
                raise ValueError("CMAPS Violation: Recovery state transition integrity violation. Status 'recovered' requires at least one failure_event.")
            if not payload["recovery_checkpoints"]:
                raise ValueError("CMAPS Violation: Recovery state transition integrity violation. Status 'recovered' requires at least one recovery_checkpoint.")

        # current_task_id not in subtask_ids
        if current_task_id in subtask_ids:
            raise ValueError(
                f"CMAPS Violation: Relational loop detected. 'current_task_id' ('{current_task_id}') "
                f"is listed as one of its own 'subtask_ids'."
            )

        # Unique decision_id values
        seen_decision_ids = set()
        for dec in payload["decision_events"]:
            dec_id = dec["decision_id"]
            if dec_id in seen_decision_ids:
                raise ValueError(f"CMAPS Violation: Duplicate decision ID detected: '{dec_id}'.")
            seen_decision_ids.add(dec_id)

        # Unique rehydration tokens
        seen_tokens = set()
        for chk in payload["recovery_checkpoints"]:
            token = chk["rehydration_token"]
            if token in seen_tokens:
                raise ValueError(f"CMAPS Violation: Duplicate rehydration token detected: '{token}'.")
            seen_tokens.add(token)

        # 6. Read-only verification metadata response
        return {
            "audit_id": payload["audit_id"],
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "SCHEMA_VALIDATED",
            "read_only_assertion": True,
        }


class SessionStateTaskLinker:
    """Enforces deep read-only lineage validation mapping SessionState to AgentTasks.

    Under Milestone 2A rules, this class operates strictly in a read-only, non-mutating
    fashion, verifying relationships and generating mapped lineage models.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize session state task linker."""
        self.validation_mode = validation_mode

    def validate_session_task_lineage(
        self,
        session: Any,  # Expected: SessionState (or dictionary)
        tasks: List[Any],  # Expected: List[AgentTask] (or dictionaries)
    ) -> Dict[str, Any]:
        """Validates that all tasks belong logically to the given session.

        Raises:
            ValueError: On objective mismatch, invalid identifier format, duplicate task ID,
                        or other lineage violations.
        """
        # 1. Extract and validate session_id
        if hasattr(session, "session_id"):
            session_id = session.session_id
        elif isinstance(session, dict) and "session_id" in session:
            session_id = session["session_id"]
        else:
            raise ValueError("SAGE-ACT Contract Violation: Missing 'session_id' in session state.")

        if not isinstance(session_id, str) or not session_id.startswith("session_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid session_id format: '{session_id}'")

        # 2. Extract active_objectives
        if hasattr(session, "active_objectives"):
            active_objectives = session.active_objectives
        elif isinstance(session, dict) and "active_objectives" in session:
            active_objectives = session["active_objectives"]
        else:
            active_objectives = []

        # 3. Process and validate tasks
        seen_task_ids = set()
        mapped_tasks = []

        for task in tasks:
            # Extract task_id
            if hasattr(task, "task_id"):
                task_id = task.task_id
            elif isinstance(task, dict) and "task_id" in task:
                task_id = task["task_id"]
            else:
                raise ValueError("SAGE-ACT Contract Violation: Missing 'task_id' in task.")

            # Extract objective_id
            if hasattr(task, "objective_id"):
                objective_id = task.objective_id
            elif isinstance(task, dict) and "objective_id" in task:
                objective_id = task["objective_id"]
            else:
                raise ValueError("SAGE-ACT Contract Violation: Missing 'objective_id' in task.")

            # Validate task_id format
            if not isinstance(task_id, str) or not task_id.startswith("task_"):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{task_id}'")

            # Duplicate task detection
            if task_id in seen_task_ids:
                raise ValueError(f"SAGE-ACT Contract Violation: Duplicate task ID detected: '{task_id}'")
            seen_task_ids.add(task_id)

            # Objective mismatch detection
            if objective_id not in active_objectives:
                raise ValueError(
                    f"SAGE-ACT Contract Violation: Objective mismatch. Task '{task_id}' maps to objective '{objective_id}', "
                    f"which is not present in session active objectives: {active_objectives}"
                )

            mapped_tasks.append(task_id)

        # Return structured lineage metadata
        return {
            "session_id": session_id,
            "mapped_tasks": mapped_tasks,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "LINEAGE_VALIDATED",
            "read_only_assertion": True,
        }


class TaskDecisionBinder:
    """Enforces read-only schema mapping and validation for Task-to-Decision lineage.

    Under Milestone 1 rules, this class operates strictly in a read-only, non-mutating
    fashion, verifying structures and generating mapping decision models.
    """

    def __init__(self, validation_mode: str = "strict"):
        """Initialize binder contract."""
        self.validation_mode = validation_mode

    def bind_task_to_decisions(self, task_id: str, decision_ids: List[str]) -> Dict[str, Any]:
        """Perform schema validation and return a read-only mapped task-to-decision lineage.

        Args:
            task_id: The target task identifier.
            decision_ids: A list of decision identifiers to bind.

        Returns:
            A dictionary representing the verified mapped decision lineage.

        Raises:
            ValueError: If task_id or decision_ids fail structural format checks.
        """
        if not task_id or not task_id.startswith("task_"):
            raise ValueError(f"SAGE-ACT Contract Violation: Invalid task_id format: '{task_id}'")

        for dec_id in decision_ids:
            if not dec_id or not (dec_id.startswith("decision_") or dec_id.startswith("proposal_")):
                raise ValueError(f"SAGE-ACT Contract Violation: Invalid decision/proposal ID format: '{dec_id}'")

        # Bind and return the structured lineage without writing or mutating system files
        return {
            "task_id": task_id,
            "bound_decisions": list(decision_ids),
            "bound_at": datetime.now(timezone.utc).isoformat(),
            "validation_status": "INTERFACE_VERIFIED",
            "read_only_assertion": True,
        }
