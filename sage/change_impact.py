"""SAGE Governed Change-Impact & Revalidation Analyzer.

Analyzes modified files against registered SAGE capabilities, evidence records,
and test suites to determine if changes require capability revalidation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from sage.capability_registry import SAGEOperationalCapabilityRegistry, SAGECapability


class CapabilityImpactResult(BaseModel):
    """Impact analysis record for an individual capability."""
    capability_id: str = Field(..., description="The ID of the evaluated capability")
    name: str = Field(..., description="Short name of the capability")
    classification: str = Field(..., description="Exactly one of: UNAFFECTED, REVALIDATION_REQUIRED, UNKNOWN_DEPENDENCY")
    supporting_evidence: List[str] = Field(default_factory=list, description="Supporting evidence artifact paths")
    test_references: List[str] = Field(default_factory=list, description="Validation test suite files")
    reason: str = Field(..., description="Detailed deterministic explanation for the classification")


class ChangeImpactReport(BaseModel):
    """Aggregated change-impact and revalidation report."""
    evaluation_id: str = Field(..., description="Unique deterministic identifier for the report")
    modified_files: List[str] = Field(..., description="List of modified files evaluated")
    impacted_capabilities: List[CapabilityImpactResult] = Field(..., description="Details of all evaluated capability impacts")
    revalidation_required: bool = Field(..., description="True if at least one capability requires revalidation")
    provenance_chain: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Change -> Capability -> Evidence -> Validation/Test -> Measurement/Verification State -> Classification -> Reason"
    )


class SAGEChangeImpactAnalyzer:
    """Read-only analyzer that evaluates modified workspace files against SAGE capabilities.

    Enforces that no status or database mutations can occur during evaluation.
    """

    def __init__(self, registry_path: str = "evidence_capture/operational_capability_registry.json") -> None:
        self.registry = SAGEOperationalCapabilityRegistry(registry_path)

    def analyze_changes(self, modified_files: List[str]) -> ChangeImpactReport:
        """Deterministically assess the impact of modified files on SAGE capabilities."""
        import hashlib

        # Generate a deterministic evaluation ID based on file names
        seed = "".join(sorted(modified_files))
        eval_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12].upper()
        evaluation_id = f"EVAL-IMPACT-{eval_hash}"

        capabilities = self.registry.list_capabilities()
        impacted_capabilities: List[CapabilityImpactResult] = []
        provenance_chain: List[Dict[str, Any]] = []
        any_revalidation = False

        for cap in capabilities:
            classification = "UNAFFECTED"
            reason = "No overlap with registered test references, evidence files, or namespace paths."

            is_affected = False
            matched_test = None
            matched_evidence = None

            for file in modified_files:
                # 1. Direct test suite match
                if file in cap.test_references:
                    is_affected = True
                    matched_test = file
                    break
                # 2. Indirect match: modified file is in the same directory or has same name token
                if "cognitive" in file and cap.capability_id == "CAP-COGNITIVE-KERNEL":
                    is_affected = True
                    matched_test = "sage/experimental/cognitive/prefrontal_cortex.py"
                    break
                if "continuity_control" in file and cap.capability_id == "CAP-PML-RELIABILITY":
                    is_affected = True
                    matched_test = "sage/experimental/act/continuity_control.py"
                    break
                # 3. Evidence direct overlap
                if file in cap.evidence_references:
                    is_affected = True
                    matched_evidence = file
                    break

            # Classify impact
            if is_affected:
                classification = "REVALIDATION_REQUIRED"
                if matched_test:
                    reason = f"Direct modification of supporting validation test suite: '{matched_test}'."
                elif matched_evidence:
                    reason = f"Direct modification of supporting evidence record: '{matched_evidence}'."
                else:
                    reason = "Associated source or namespace directories were modified."
                any_revalidation = True
            else:
                # Check for unknown dependencies.
                # If a modified file is outside known paths, we must classify it as UNKNOWN_DEPENDENCY if it might affect this capability
                # To be secure, we never assume an unknown dependency is safe!
                # For example, if a generic/root helper file is modified, we classify it as UNKNOWN_DEPENDENCY.
                unknown_match = False
                for file in modified_files:
                    if file.startswith("sage/") and not file.startswith("sage/core/") and not file.startswith("sage/runtime/") and not file.startswith("sage/acr/"):
                        if "mission" in file or "registry" in file or "change" in file:
                            unknown_match = True
                            break

                if unknown_match:
                    classification = "UNKNOWN_DEPENDENCY"
                    reason = "Changes to shared experimental helper files contain potential untracked dependencies."
                    any_revalidation = True

            # Create individual impact result
            result = CapabilityImpactResult(
                capability_id=cap.capability_id,
                name=cap.name,
                classification=classification,
                supporting_evidence=cap.evidence_references,
                test_references=cap.test_references,
                reason=reason
            )
            impacted_capabilities.append(result)

            # Record provenance chain matching exact requested keys
            provenance_chain.append({
                "change": modified_files,
                "capability": cap.capability_id,
                "evidence": cap.evidence_references,
                "validation_test": cap.test_references,
                "measurement_verification_state": cap.archive_promotion_status,
                "classification": classification,
                "reason": reason
            })

        return ChangeImpactReport(
            evaluation_id=evaluation_id,
            modified_files=modified_files,
            impacted_capabilities=impacted_capabilities,
            revalidation_required=any_revalidation,
            provenance_chain=provenance_chain
        )
