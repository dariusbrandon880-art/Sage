from typing import Dict, Any
from sage.runtime.interceptors.bond.errors import AmbiguousPayloadError, MissingSchemaFieldsError

class PayloadExtractor:
    """Extracts and performs static checks on validation payload maps."""

    @staticmethod
    def extract_and_check_ambiguity(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        # Check for ambiguity: conflicting state destination parameters
        if "target_state" in raw_payload and "state_destination" in raw_payload:
            raise AmbiguousPayloadError("Conflicting parameters 'target_state' and 'state_destination' are both present")

        # Check for missing required schema keys
        required_fields = ["tx_id", "auth_token", "identity_ref", "target_state", "evidence_refs"]
        for field in required_fields:
            if field not in raw_payload:
                raise MissingSchemaFieldsError(f"Required schema field '{field}' is missing from payload")

        return raw_payload
