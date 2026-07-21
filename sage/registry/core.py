"""Core implementation of the SAGE Capability Registry."""

from typing import List, Dict, Any, Optional, Callable
from sage.registry.models import Capability


class CapabilityRegistry:
    """Registry to define, store, and dynamically execute capabilities."""

    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.handlers: Dict[str, Callable[..., Any]] = {}

    def register_capability(self, capability: Capability, handler: Optional[Callable[..., Any]] = None) -> None:
        """Register a new capability and its optional execution handler."""
        self.capabilities[capability.id] = capability
        if handler:
            self.handlers[capability.id] = handler

    def retrieve_capability(self, capability_id: str) -> Optional[Capability]:
        """Retrieve a registered capability by its ID."""
        return self.capabilities.get(capability_id)

    def list_capabilities(self, active_only: bool = True) -> List[Capability]:
        """List registered capabilities, optionally filtered by active status."""
        if active_only:
            return [c for c in self.capabilities.values() if c.active]
        return list(self.capabilities.values())

    def invoke_capability(self, capability_id: str, args: Dict[str, Any], scopes: List[str]) -> Any:
        """Dynamically invoke a registered capability if permission scopes match."""
        capability = self.retrieve_capability(capability_id)
        if not capability:
            raise ValueError(f"Capability with ID '{capability_id}' not found.")

        if not capability.active:
            raise ValueError(f"Capability with ID '{capability_id}' is inactive.")

        # Validate permission scopes
        for perm in capability.permissions:
            if perm not in scopes:
                raise PermissionError(
                    f"Required permission scope '{perm}' is missing from user scopes: {scopes}."
                )

        handler = self.handlers.get(capability_id)
        if not handler:
            raise NotImplementedError(
                f"No executable handler registered for capability '{capability_id}'."
            )

        return handler(**args)
