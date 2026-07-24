"""SAGE Security Boundary Enforcement under SPEK v1.1."""

from typing import Dict, Any, Optional


class BoundaryEnforcer:
    """Enforces logical security and permission boundaries on SPEK operations.

    Ensures that only authorized operations with valid credentials/tokens are
    permitted to mutate the Immutable Ledger, promote candidate rules, or
    interact with protected SPEK paths.
    """

    def __init__(self, required_token: str = "SAGE_SPEK_KERNEL_AUTH_TOKEN"):
        self.required_token = required_token

    def enforce_boundary_mutation(self, auth_token: Optional[str]) -> None:
        """Validate an authentication token against required security policies.

        Raises:
            PermissionError: If the token is missing, invalid, or violates boundary constraints.
        """
        if not auth_token:
            raise PermissionError("Security Boundary Violation: Mutation authorization token is missing.")

        if auth_token != self.required_token:
            raise PermissionError("Security Boundary Violation: Unauthorized attempt to mutate SPEK immutable state.")
