"""SAGE Operational Capability Registry - Governed inventory of active capabilities.

Provides a unified, governed record of implemented features, lifecycle state,
dependencies, validation status, test suites, and evidence files.
"""

import os
import json
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class SAGECapability(BaseModel):
    """Schema representing an individual SAGE capability."""
    capability_id: str = Field(...)
    name: str = Field(...)
    description: str = Field(...)
    implementation_status: str = Field("IMPLEMENTED")
    validation_status: str = Field("VALIDATED")
    lifecycle_status: str = Field(
        "ACTIVE",
        description="ACTIVE, PARTIAL, BLOCKED, DEPRECATED, or RESEARCH_ONLY."
    )
    dependencies: List[str] = Field(default_factory=list)
    lineage_references: List[str] = Field(default_factory=list)
    incompletion_reason: Optional[str] = Field(default=None)
    evidence_references: List[str] = Field(default_factory=list)
    test_references: List[str] = Field(default_factory=list)
    archive_promotion_status: str = Field("READY")


class SAGEOperationalCapabilityRegistry:
    """Manager for SAGE Operational Capabilities, providing persistence and lookup."""

    def __init__(self, storage_path: str = "evidence_capture/operational_capability_registry.json"):
        self.storage_path = storage_path
        self.capabilities: Dict[str, SAGECapability] = {}
        self.load()

    def get_default_capabilities(self) -> List[SAGECapability]:
        """Generate the baseline of pre-validated SAGE capabilities."""
        return [
            SAGECapability(capability_id="CAP-STATE-PERSISTENCE", name="State Persistence", description="Continuous, atomic serialization of active objectives and task states.", evidence_references=["evidence_capture/ccl_operational_feedback.json"], test_references=["tests/test_continuity_persistence.py"]),
            SAGECapability(capability_id="CAP-CHECKPOINTING", name="State Checkpointing", description="On-demand, full database and state serialization checkpoints with rollback.", evidence_references=["evidence_capture/ccl_operational_feedback.json"], test_references=["tests/test_continuity_intelligence.py"]),
            SAGECapability(capability_id="CAP-HANDOFF-GENERATION", name="Handoff Generation", description="Exporting full system context and session lineage for handoff transitions.", evidence_references=["evidence_capture/ccl_operational_feedback.json"], test_references=["tests/test_new_systems.py"]),
            SAGECapability(capability_id="CAP-WORKSPACE-SNAPSHOTS", name="Workspace Snapshots", description="Granular snapshots stored under .sage/sage_state.json for fast reboot hydration.", evidence_references=["evidence_capture/ccl_operational_feedback.json"], test_references=["tests/test_continuity_intelligence.py"]),
            SAGECapability(capability_id="CAP-CONTINUITY-BRIDGE", name="Continuity Bridge", description="Single authoritative ingestion pipeline mapping raw interactions into state.", evidence_references=["evidence_capture/ccl_operational_feedback.json"], test_references=["tests/test_continuity_bridge.py"]),
            SAGECapability(capability_id="CAP-COGNITIVE-KERNEL", name="Cognitive Kernel Foundation", description="High-fidelity prefrontal cortex safety gates, agent constraints, and decision evaluations.", evidence_references=["evidence_capture/cognitive_kernel_foundation_report.json"], test_references=["tests/experimental/test_cognitive_kernel.py"]),
            SAGECapability(capability_id="CAP-PML-RELIABILITY", name="PML Operational Reliability", description="Cryptographic hash chains, sequence validation, and truncation/rollback tampering detection.", evidence_references=["evidence_capture/ccl_orchestrator_evidence.json"], test_references=["tests/experimental/test_continuity_control.py"]),
        ]

    def load(self) -> None:
        """Load capabilities, preserving backward compatibility with legacy records."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    cap = SAGECapability(**item)
                    self.capabilities[cap.capability_id] = cap
                return
            except Exception as exc:
                print(f"[*] Warning loading capability registry: {exc}. Re-seeding defaults.")

        for cap in self.get_default_capabilities():
            self.capabilities[cap.capability_id] = cap
        self.save()

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump([cap.model_dump() for cap in self.capabilities.values()], f, indent=2)

    def add_capability(self, capability: SAGECapability) -> None:
        self.capabilities[capability.capability_id] = capability
        self.save()

    def get_capability(self, capability_id: str) -> Optional[SAGECapability]:
        return self.capabilities.get(capability_id)

    def lookup_by_name(self, name: str) -> Optional[SAGECapability]:
        name_lower = name.lower()
        for cap in self.capabilities.values():
            if cap.name.lower() == name_lower:
                return cap
        return None

    def list_capabilities(self) -> List[SAGECapability]:
        return list(self.capabilities.values())
