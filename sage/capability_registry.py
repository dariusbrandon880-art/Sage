"""SAGE Operational Capability Registry - Governed inventory of active capabilities.

Provides a unified, governed record of all implemented features, linking
implementation status, validation status, test suites, and evidence files.
"""

import os
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SAGECapability(BaseModel):
    """Schema representing an individual SAGE capability."""
    capability_id: str = Field(
        ...,
        description="Unique identifier for the capability, e.g., CAP-COGNITIVE-KERNEL"
    )
    name: str = Field(
        ...,
        description="Short, human-readable name of the capability"
    )
    description: str = Field(
        ...,
        description="Detailed description of the capability's purpose and functionality"
    )
    implementation_status: str = Field(
        "IMPLEMENTED",
        description="Status of the implementation (e.g., IMPLEMENTED, DEPRECATED)"
    )
    validation_status: str = Field(
        "VALIDATED",
        description="Status of verification and testing (e.g., VALIDATED, UNVERIFIED)"
    )
    evidence_references: List[str] = Field(
        default_factory=list,
        description="Paths to JSON files or other evidence tracking this capability"
    )
    test_references: List[str] = Field(
        default_factory=list,
        description="Unit or integration test files verifying correctness"
    )
    archive_promotion_status: str = Field(
        "READY",
        description="Readiness state for canonical SAGE Archive promotion (e.g., READY, PROMOTED)"
    )
    lifecycle_status: str = Field(
        "VALIDATED",
        description="Lifecycle status of the capability (e.g., VALIDATED, PARTIAL, DEPRECATED)"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of capability IDs this capability depends upon"
    )
    incompletion_reason: Optional[str] = Field(
        None,
        description="Reason for incompletion if lifecycle_status is PARTIAL or incomplete"
    )


class SAGEOperationalCapabilityRegistry:
    """Manager for SAGE Operational Capabilities, providing persistence and lookup."""

    def __init__(self, storage_path: str = "evidence_capture/operational_capability_registry.json"):
        self.storage_path = storage_path
        self.capabilities: Dict[str, SAGECapability] = {}
        self.load()

    def get_default_capabilities(self) -> List[SAGECapability]:
        """Generate the baseline of pre-validated SAGE capabilities."""
        return [
            SAGECapability(
                capability_id="CAP-STATE-PERSISTENCE",
                name="State Persistence",
                description="Continuous, atomic serialization of active objectives and task states.",
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=["evidence_capture/ccl_operational_feedback.json"],
                test_references=["tests/test_continuity_persistence.py"],
                archive_promotion_status="READY"
            ),
            SAGECapability(
                capability_id="CAP-CHECKPOINTING",
                name="State Checkpointing",
                description="On-demand, full database and state serialization checkpoints with rollback.",
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=["evidence_capture/ccl_operational_feedback.json"],
                test_references=["tests/test_continuity_intelligence.py"],
                archive_promotion_status="READY"
            ),
            SAGECapability(
                capability_id="CAP-HANDOFF-GENERATION",
                name="Handoff Generation",
                description="Exporting full system context and session lineage for handoff transitions.",
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=["evidence_capture/ccl_operational_feedback.json"],
                test_references=["tests/test_new_systems.py"],
                archive_promotion_status="READY"
            ),
            SAGECapability(
                capability_id="CAP-WORKSPACE-SNAPSHOTS",
                name="Workspace Snapshots",
                description="Granular snapshots stored under .sage/sage_state.json for fast reboot hydration.",
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=["evidence_capture/ccl_operational_feedback.json"],
                test_references=["tests/test_continuity_intelligence.py"],
                archive_promotion_status="READY"
            ),
            SAGECapability(
                capability_id="CAP-CONTINUITY-BRIDGE",
                name="Continuity Bridge",
                description="Single authoritative ingestion pipeline mapping raw interactions into state.",
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=["evidence_capture/ccl_operational_feedback.json"],
                test_references=["tests/test_continuity_bridge.py"],
                archive_promotion_status="READY"
            ),
            SAGECapability(
                capability_id="CAP-COGNITIVE-KERNEL",
                name="Cognitive Kernel Foundation",
                description="High-fidelity prefrontal cortex safety gates, agent constraints, and decision evaluations.",
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=["evidence_capture/cognitive_kernel_foundation_report.json"],
                test_references=["tests/experimental/test_cognitive_kernel.py"],
                archive_promotion_status="READY"
            ),
            SAGECapability(
                capability_id="CAP-PML-RELIABILITY",
                name="PML Operational Reliability",
                description="Cryptographic hash chains, sequence validation, and truncation/rollback tampering detection.",
                implementation_status="IMPLEMENTED",
                validation_status="VALIDATED",
                evidence_references=["evidence_capture/ccl_orchestrator_evidence.json"],
                test_references=["tests/experimental/test_continuity_control.py"],
                archive_promotion_status="READY"
            )
        ]

    def load(self) -> None:
        """Load capabilities from the JSON storage file, or seed defaults if not present."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        cap = SAGECapability(**item)
                        self.capabilities[cap.capability_id] = cap
                return
            except Exception as e:
                print(f"[*] Warning loading capability registry: {e}. Re-seeding defaults.")

        # Seed defaults
        defaults = self.get_default_capabilities()
        for cap in defaults:
            self.capabilities[cap.capability_id] = cap
        self.save()

    def save(self) -> None:
        """Serialize all registered capabilities to the JSON storage path."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        serialized = [cap.model_dump() for cap in self.capabilities.values()]
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2)

    def add_capability(self, capability: SAGECapability) -> None:
        """Add or update a capability in the registry and persist changes."""
        self.capabilities[capability.capability_id] = capability
        self.save()

    def get_capability(self, capability_id: str) -> Optional[SAGECapability]:
        """Retrieve a registered capability by its unique ID."""
        return self.capabilities.get(capability_id)

    def lookup_by_name(self, name: str) -> Optional[SAGECapability]:
        """Perform lookup to find a capability by its human-readable name."""
        name_lower = name.lower()
        for cap in self.capabilities.values():
            if cap.name.lower() == name_lower:
                return cap
        return None

    def list_capabilities(self) -> List[SAGECapability]:
        """Return a flat list of all registered capabilities."""
        return list(self.capabilities.values())
