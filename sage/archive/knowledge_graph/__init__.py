"""Intelligent Knowledge Graph representing connected nodes and edges in SAGE archive."""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from sage.archive.relationships import KnowledgeRelationship


class KnowledgeGraph(BaseModel):
    """SAGE Knowledge Graph traversing nodes (ArchiveEntries) and relationships."""

    nodes: Set[str] = Field(default_factory=set)  # Archive entry IDs
    edges: List[KnowledgeRelationship] = Field(default_factory=list)

    def add_node(self, node_id: str) -> None:
        """Add a node to the graph."""
        self.nodes.add(node_id)

    def add_relationship(self, relationship: KnowledgeRelationship) -> None:
        """Add a relationship/edge to the graph."""
        self.add_node(relationship.source_id)
        self.add_node(relationship.target_id)
        # Check if already exists to avoid duplicates
        exists = any(
            r.source_id == relationship.source_id
            and r.target_id == relationship.target_id
            and r.relationship_type == relationship.relationship_type
            for r in self.edges
        )
        if not exists:
            self.edges.append(relationship)

    def get_relationships_for_node(self, node_id: str) -> List[KnowledgeRelationship]:
        """Get all relationships involving a specific node."""
        return [r for r in self.edges if r.source_id == node_id or r.target_id == node_id]

    def get_related_nodes(self, node_id: str, relationship_type: Optional[str] = None) -> List[str]:
        """Get IDs of all nodes connected to a node, optionally filtered by type."""
        related = []
        for r in self.edges:
            if relationship_type and r.relationship_type != relationship_type:
                continue
            if r.source_id == node_id:
                related.append(r.target_id)
            elif r.target_id == node_id:
                related.append(r.source_id)
        return list(set(related))
