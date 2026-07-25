import copy
from typing import Dict, Any, List
from pydantic import ValidationError
from sage.runtime.interceptors.bond.errors import (
    BondError,
    AuthorityMismatchError,
    UnauthorizedIdentityMutationError,
    MalformedPayloadError,
)
from sage.runtime.interceptors.bond.schemas import StateTransitionPayload
from sage.runtime.interceptors.bond.extractor import PayloadExtractor

class BondValidator:
    """Validator layer coordinating the enforcement and shadow activation of CIV rules."""

    def __init__(self, expected_token: str = "sys_trust_token_abc", mode: str = "shadow"):
        self.expected_token = expected_token
        self.mode = mode.lower() # "shadow", "enforce", "disabled"
        self.audit_log: List[Dict[str, Any]] = []

    def validate_transition(self, active_state: Dict[str, Any], raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intercepts and validates the state transition.
        In 'shadow' mode: records results but never blocks the state transition.
        In 'enforce' mode: blocks transition and rolls back state upon any validation failure.
        """
        state_backup = copy.deepcopy(active_state)
        error_context = None

        try:
            # 1. Parameter extraction and static ambiguity check
            payload_map = PayloadExtractor.extract_and_check_ambiguity(raw_payload)

            # 2. Pydantic schema validation
            try:
                payload = StateTransitionPayload(**payload_map)
            except ValidationError as ve:
                raise MalformedPayloadError(str(ve))

            # 3. Authority checks
            if payload.auth_token != self.expected_token:
                raise AuthorityMismatchError()

            # 4. Identity mutation checks
            if active_state.get("identity_ref") and payload.identity_ref != active_state.get("identity_ref"):
                raise UnauthorizedIdentityMutationError()

            # Validation succeeded
            audit_entry = {
                "tx_id": payload.tx_id,
                "status": "VALIDATION_PASS",
                "mode": self.mode
            }
            self.audit_log.append(audit_entry)

            # Perform the mutation
            active_state["active_state"] = payload.target_state
            active_state["identity_ref"] = payload.identity_ref
            active_state["last_tx_id"] = payload.tx_id

            return {
                "status": "VALIDATION_PASS",
                "audit": audit_entry,
                "state": active_state
            }

        except Exception as e:
            # Determine error code and message
            if isinstance(e, BondError):
                code = e.code
                message = e.message
            else:
                code = "CIV-ERR-SYS-999"
                message = str(e)

            audit_entry = {
                "tx_id": raw_payload.get("tx_id", "unknown_tx"),
                "status": "VALIDATION_FAIL",
                "code": code,
                "message": message,
                "mode": self.mode
            }
            self.audit_log.append(audit_entry)

            if self.mode == "shadow":
                # Shadow validation: Observe and log failure but DO NOT block transition
                # Mutate active_state anyway based on raw target_state to prevent blocking
                if "target_state" in raw_payload:
                    active_state["active_state"] = raw_payload["target_state"]
                if "identity_ref" in raw_payload:
                    active_state["identity_ref"] = raw_payload["identity_ref"]
                if "tx_id" in raw_payload:
                    active_state["last_tx_id"] = raw_payload["tx_id"]

                return {
                    "status": "VALIDATION_FAIL_SHADOWED",
                    "audit": audit_entry,
                    "state": active_state
                }
            else:
                # Enforce mode: rollback state to original baseline and raise/return error
                active_state.clear()
                active_state.update(state_backup)
                return {
                    "status": "VALIDATION_FAIL",
                    "code": code,
                    "message": message,
                    "state": active_state
                }
