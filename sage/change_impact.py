"""SAGE Governed Change-Impact & Revalidation Analyzer."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sage.capability_registry import SAGEOperationalCapabilityRegistry


class CapabilityImpactResult(BaseModel):
    capability_id: str = Field(...)
    name: str = Field(...)
    classification: str = Field(...)
    supporting_evidence: List[str] = Field(default_factory=list)
    test_references: List[str] = Field(default_factory=list)
    reason: str = Field(...)


class ChangeImpactReport(BaseModel):
    evaluation_id: str = Field(...)
    modified_files: List[str] = Field(...)
    impacted_capabilities: List[CapabilityImpactResult] = Field(...)
    revalidation_required: bool = Field(...)
    provenance_chain: List[Dict[str, Any]] = Field(default_factory=list)


class SAGEChangeImpactAnalyzer:
    """Read-only analyzer with explicit dependency-path support."""

    def __init__(
        self,
        registry_path: str = "evidence_capture/operational_capability_registry.json",
        dependency_paths: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        self.registry = SAGEOperationalCapabilityRegistry(registry_path)
        self.dependency_paths = dependency_paths or {}

    def analyze_changes(self, modified_files: List[str]) -> ChangeImpactReport:
        import hashlib

        seed = "".join(sorted(modified_files))
        evaluation_id = f"EVAL-IMPACT-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12].upper()}"
        impacted_capabilities: List[CapabilityImpactResult] = []
        provenance_chain: List[Dict[str, Any]] = []
        any_revalidation = False

        for cap in self.registry.list_capabilities():
            classification = "UNAFFECTED"
            reason = "No overlap with registered tests, evidence, or declared dependency paths."
            matched_test = next((f for f in modified_files if f in cap.test_references), None)
            matched_evidence = next((f for f in modified_files if f in cap.evidence_references), None)
            matched_dependency = next(
                (f for f in modified_files if any(f == p or f.startswith(p.rstrip('/') + '/') for p in self.dependency_paths.get(cap.capability_id, []))),
                None,
            )

            if matched_test:
                classification = "REVALIDATION_REQUIRED"
                reason = f"Direct modification of supporting validation test suite: '{matched_test}'."
            elif matched_evidence:
                classification = "REVALIDATION_REQUIRED"
                reason = f"Direct modification of supporting evidence record: '{matched_evidence}'."
            elif matched_dependency:
                classification = "REVALIDATION_REQUIRED"
                reason = f"Modification of declared dependency path: '{matched_dependency}'."
            elif any(
                f.startswith("sage/") and ("mission" in f or "registry" in f or "change" in f)
                for f in modified_files
            ):
                classification = "UNKNOWN_DEPENDENCY"
                reason = "Shared SAGE helper changes have an untracked dependency surface."

            if classification != "UNAFFECTED":
                any_revalidation = True

            result = CapabilityImpactResult(
                capability_id=cap.capability_id,
                name=cap.name,
                classification=classification,
                supporting_evidence=cap.evidence_references,
                test_references=cap.test_references,
                reason=reason,
            )
            impacted_capabilities.append(result)
            provenance_chain.append({
                "change": modified_files,
                "capability": cap.capability_id,
                "evidence": cap.evidence_references,
                "validation_test": cap.test_references,
                "measurement_verification_state": cap.archive_promotion_status,
                "classification": classification,
                "reason": reason,
            })

        return ChangeImpactReport(
            evaluation_id=evaluation_id,
            modified_files=modified_files,
            impacted_capabilities=impacted_capabilities,
            revalidation_required=any_revalidation,
            provenance_chain=provenance_chain,
        )
