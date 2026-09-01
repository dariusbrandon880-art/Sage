"""SAGE Operational Capability Registry - Governed inventory of active capabilities.

Provides a unified, governed record of all implemented features, linking
implementation status, validation status, test suites, and evidence files.
"""

import os
import json
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CapabilityDisposition(str, Enum):
    """Governed lifecycle disposition for SAGE capabilities across PRs."""
    INTEGRATED = "INTEGRATED"
    RECOVERED = "RECOVERED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"
    INVALIDATED = "INVALIDATED"


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
    disposition: CapabilityDisposition = Field(
        CapabilityDisposition.INTEGRATED,
        description="Governance disposition state for lineage preservation"
    )
    pr_reference: Optional[str] = Field(
        None,
        description="Originating pull request reference (e.g., PR #266)"
    )
    disposition_reason: Optional[str] = Field(
        None,
        description="Reasoning or evidence provenance behind the current capability disposition"
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

    def reconcile_pr_capability(
        self,
        capability_id: str,
        name: str,
        description: str,
        pr_reference: str,
        evidence_references: Optional[List[str]] = None,
        test_references: Optional[List[str]] = None,
        disposition: CapabilityDisposition = CapabilityDisposition.RECOVERED,
        disposition_reason: Optional[str] = None,
    ) -> SAGECapability:
        """Reconciles a historical or active recovery lane PR capability against current main."""
        evidence_refs = evidence_references or []
        test_refs = test_references or []

        existing = self.get_capability(capability_id)
        if existing:
            existing.disposition = disposition
            existing.pr_reference = pr_reference
            existing.disposition_reason = disposition_reason or f"Reconciled against current main via {pr_reference}"
            if evidence_refs:
                existing.evidence_references = list(dict.fromkeys(existing.evidence_references + evidence_refs))
            if test_refs:
                existing.test_references = list(dict.fromkeys(existing.test_references + test_refs))
            self.save()
            return existing

        cap = SAGECapability(
            capability_id=capability_id,
            name=name,
            description=description,
            implementation_status="IMPLEMENTED",
            validation_status="VALIDATED" if evidence_refs else "UNVERIFIED",
            evidence_references=evidence_refs,
            test_references=test_refs,
            archive_promotion_status="READY",
            disposition=disposition,
            pr_reference=pr_reference,
            disposition_reason=disposition_reason or f"Reconciled from recovery lane {pr_reference}",
        )
        self.add_capability(cap)
        return cap

    def get_capabilities_by_disposition(self, disposition: CapabilityDisposition) -> List[SAGECapability]:
        """Filter and return capabilities by their governed disposition state."""
        return [cap for cap in self.capabilities.values() if cap.disposition == disposition]

    def audit_registry_health(self) -> Dict[str, Any]:
        """Perform diagnostic audit over operational capability registry health."""
        all_caps = self.list_capabilities()
        return {
            "total_capabilities": len(all_caps),
            "validated_count": sum(1 for c in all_caps if c.validation_status == "VALIDATED"),
            "ready_count": sum(1 for c in all_caps if c.archive_promotion_status == "READY"),
            "dispositions": {
                disp.value: sum(1 for c in all_caps if c.disposition == disp)
                for disp in CapabilityDisposition
            },
        }

    def sync_from_capability_graph(self, repo_root: str = ".") -> int:
        """Discovers repository capability surface and registers newly validated/tested nodes."""
        from sage.c2.capability_graph import CapabilityGraphEngine

        engine = CapabilityGraphEngine(repo_root=repo_root)
        nodes = engine.discover_repository_capabilities()

        added_count = 0
        for cap_id, node in nodes.items():
            if cap_id in self.capabilities:
                continue

            cap = SAGECapability(
                capability_id=f"CAP-{cap_id.upper().replace('.', '-')}",
                name=node.name,
                description=node.description or f"Auto-discovered capability from {node.source_path}",
                implementation_status=node.status.value,
                validation_status="VALIDATED" if node.test_paths else "UNVERIFIED",
                evidence_references=[],
                test_references=list(node.test_paths),
                archive_promotion_status="READY",
                disposition=CapabilityDisposition.INTEGRATED,
            )
            self.capabilities[cap.capability_id] = cap
            added_count += 1

        if added_count > 0:
            self.save()

        return added_count
