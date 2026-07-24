"""SAGE ACR-X Memory Fabric.

Manages isolated memory storage, indexing, and retrieval across
WORKING, EPISODIC, SEMANTIC, and PROCEDURAL layers.
"""

from sage.core.acrx_models import MemoryToken, STPMemoryLayer


class ACRXMemoryFabric:
    """Memory Fabric managing four isolated memory layers."""

    def __init__(self):
        """Initialize memory layer stores."""
        self.stores: dict[STPMemoryLayer, dict[str, MemoryToken]] = {
            STPMemoryLayer.WORKING: {},
            STPMemoryLayer.EPISODIC: {},
            STPMemoryLayer.SEMANTIC: {},
            STPMemoryLayer.PROCEDURAL: {},
        }

    def store_token(self, token: MemoryToken) -> None:
        """Store a MemoryToken under its specified isolated layer."""
        self.stores[token.layer][token.token_id] = token

    def retrieve_token(self, token_id: str) -> MemoryToken | None:
        """Search and retrieve a token by its identity ID across all layers."""
        for layer_store in self.stores.values():
            if token_id in layer_store:
                return layer_store[token_id]
        return None

    def list_layer_tokens(self, layer: STPMemoryLayer) -> list[MemoryToken]:
        """List all MemoryTokens stored inside the specified layer."""
        return list(self.stores[layer].values())
