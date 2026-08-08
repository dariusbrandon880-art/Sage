"""SAGE Change-Impact & Revalidation Analyzer (SAGE-CIRA).

Analyzes the cascading validation impact of capability changes across SAGE
dependent capabilities, evidence records, and verification claims.
"""

from typing import Any, Dict, List, Set
from sage.experimental.act.capability_passport import CapabilityPassport


class SAGEChangeImpactAnalyzer:
    """Read-only analyzer to evaluate cascading capability change impacts."""

    def __init__(self, passports: List[CapabilityPassport]):
        self.passports = {p.name: p for p in passports}

    def analyze_impact(self, changed_capability_name: str) -> Dict[str, Any]:
        """Deterministically evaluates dependencies, evidence, and claims affected by a change.

        Allowed classifications ONLY:
        - UNAFFECTED
        - REVALIDATION_REQUIRED
        - UNKNOWN_DEPENDENCY
        """
        if changed_capability_name not in self.passports:
            # Build unknown dependency responses for all known passports plus the unknown target
            assessments = {}
            for name, p in self.passports.items():
                assessments[name] = {
                    "change_origin": changed_capability_name,
                    "affected_capability": name,
                    "supporting_evidence": p.evidence_path,
                    "validation_test": p.validation_strategy,
                    "measurement_verification_state": "PROPOSED_PASSPORT",
                    "classification": "UNKNOWN_DEPENDENCY",
                    "reason": f"Dependency on '{changed_capability_name}' is unestablished or missing."
                }
            assessments[changed_capability_name] = {
                "change_origin": changed_capability_name,
                "affected_capability": changed_capability_name,
                "supporting_evidence": "",
                "validation_test": "",
                "measurement_verification_state": "PROPOSED_PASSPORT",
                "classification": "UNKNOWN_DEPENDENCY",
                "reason": f"Capability '{changed_capability_name}' is not registered in the passport registry."
            }

            return {
                "changed_capability": changed_capability_name,
                "status": "UNKNOWN_DEPENDENCY",
                "reason": f"Capability '{changed_capability_name}' is not registered in the passport registry.",
                "impacted_capabilities_count": 0,
                "revalidation_required_files_count": 0,
                "revalidation_required_files": [],
                "assessments": assessments
            }

        # Compute direct and transitive dependencies (BFS/DFS traversal of the dependency tree)
        impacted_capabilities: Dict[str, Dict[str, Any]] = {}
        revalidation_required_files: Set[str] = set()

        # Queue for traversal, starting with direct dependents of changed_capability_name
        queue: List[str] = []
        visited: Set[str] = {changed_capability_name}

        # Find direct dependents
        for name, p in self.passports.items():
            if changed_capability_name in p.dependencies:
                queue.append(name)
                visited.add(name)
                impacted_capabilities[name] = {
                    "impact_tier": "DIRECT",
                    "provenance": f"Directly depends on changed capability '{changed_capability_name}'"
                }
                if p.evidence_path:
                    revalidation_required_files.add(p.evidence_path)

        # Transitive dependents traversal
        while queue:
            current = queue.pop(0)
            for name, p in self.passports.items():
                if name not in visited and current in p.dependencies:
                    queue.append(name)
                    visited.add(name)
                    impacted_capabilities[name] = {
                        "impact_tier": "TRANSITIVE",
                        "provenance": f"Transitively depends on changed capability '{changed_capability_name}' via '{current}'"
                    }
                    if p.evidence_path:
                        revalidation_required_files.add(p.evidence_path)

        # Build final report
        assessments: Dict[str, Dict[str, Any]] = {}
        for name, p in self.passports.items():
            if name == changed_capability_name:
                classification = "REVALIDATION_REQUIRED"
                reason = "This is the source of the capability changes."
            elif name in impacted_capabilities:
                classification = "REVALIDATION_REQUIRED"
                reason = impacted_capabilities[name]["provenance"]
            else:
                classification = "UNAFFECTED"
                reason = f"No direct or transitive dependency on '{changed_capability_name}' exists."

            assessments[name] = {
                "change_origin": changed_capability_name,
                "affected_capability": name,
                "supporting_evidence": p.evidence_path,
                "validation_test": p.validation_strategy,
                "measurement_verification_state": "VERIFIED_PASSPORT" if p.lifecycle_state == "VALIDATED" else "PROPOSED_PASSPORT",
                "classification": classification,
                "reason": reason
            }

        return {
            "changed_capability": changed_capability_name,
            "status": "ANALYZED",
            "impacted_capabilities_count": len(impacted_capabilities),
            "revalidation_required_files_count": len(revalidation_required_files),
            "revalidation_required_files": sorted(list(revalidation_required_files)),
            "assessments": assessments
        }
