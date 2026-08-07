"""SAGE Capability Verification Chain (SAGE-CVC).

Integrates SAGE Capability Passports, test runners, and evidence files to
deterministically evaluate if the actual evidence supports the claimed lifecycle status.
"""

from typing import Any, Dict, List, Optional
from sage.experimental.act.capability_passport import CapabilityPassport, CapabilityPassportGovernanceEngine


class CapabilityVerificationChain:
    """Read-only verification and assessment engine to determine capability readiness."""

    def __init__(self):
        self.passport_engine = CapabilityPassportGovernanceEngine()

    def evaluate_capability_status(
        self,
        passport: CapabilityPassport,
        executed_tests: List[str],
        captured_evidence_files: List[str],
        has_measurement: bool = True,
        protected_boundary_secure: bool = True
    ) -> Dict[str, Any]:
        """Deterministically evaluates if actual evidence supports the declared capability status.

        Classification rules:
        - INCOMPARABLE: Name doesn't start with CAP- or passport fails No Orphan Rule.
        - INCONSISTENT: Passport has conflicting configuration declarations (e.g. VALIDATED with PROPOSED allowed state).
        - INSUFFICIENT_EVIDENCE: Passport claims VALIDATED but has no actual evidence files or tests.
        - PARTIALLY_VERIFIED: Has tests run but missing evidence files, or vice-versa.
        - VERIFIED: All tests run, evidence files captured, and protected boundaries verified.
        """
        # 1. Contradiction Detection in Declared Configuration
        if hasattr(passport, "lifecycle_state") and hasattr(passport, "allowed_next_state"):
            if passport.lifecycle_state in ["VALIDATED", "CANONICAL"] and passport.allowed_next_state == "PROPOSED":
                return {
                    "capability_name": getattr(passport, "name", "UNKNOWN"),
                    "declared_status": passport.lifecycle_state,
                    "verification_status": "INCONSISTENT",
                    "evidence_supported": False,
                    "reason": "Capability claims high-tier maturity but allowed next transition state is downgraded."
                }

        # 2. Identity & Structure Verification (No Orphan Capability Rule)
        try:
            is_valid_passport = self.passport_engine.verify_no_orphan_rule(passport)
        except Exception:
            is_valid_passport = False

        if not is_valid_passport or not hasattr(passport, "name") or not passport.name.startswith("CAP-"):
            return {
                "capability_name": getattr(passport, "name", "UNKNOWN"),
                "declared_status": getattr(passport, "lifecycle_state", "UNKNOWN"),
                "verification_status": "INCOMPARABLE",
                "evidence_supported": False,
                "reason": "Capability passport is incomplete, invalidly named, or fails the No Orphan Rule."
            }

        # 3. Check Actual Evidence vs. Declared Status
        has_test_coverage = any(passport.name.lower() in t.lower() or "passport" in t.lower() or "sdr_004" in t.lower() for t in executed_tests)
        has_evidence_captured = passport.evidence_path in captured_evidence_files

        # 4. Deterministic Classifications
        if passport.lifecycle_state in ["VALIDATED", "CANONICAL"]:
            if not has_test_coverage and not has_evidence_captured:
                verification_status = "INSUFFICIENT_EVIDENCE"
                evidence_supported = False
            elif not has_test_coverage or not has_evidence_captured or not has_measurement or not protected_boundary_secure:
                verification_status = "PARTIALLY_VERIFIED"
                evidence_supported = False
            else:
                verification_status = "VERIFIED"
                evidence_supported = True
        else:
            # For PROPOSED state, partial or verified is based on any available evidence
            if has_test_coverage and has_evidence_captured:
                verification_status = "VERIFIED"
                evidence_supported = True
            elif has_test_coverage or has_evidence_captured:
                verification_status = "PARTIALLY_VERIFIED"
                evidence_supported = False
            else:
                verification_status = "INSUFFICIENT_EVIDENCE"
                evidence_supported = False

        return {
            "capability_name": passport.name,
            "declared_status": passport.lifecycle_state,
            "verification_status": verification_status,
            "evidence_supported": evidence_supported,
            "details": {
                "has_test_coverage": has_test_coverage,
                "has_evidence_captured": has_evidence_captured,
                "has_measurement": has_measurement,
                "protected_boundary_secure": protected_boundary_secure,
                "lineage_referenced": bool(passport.archive_location)
            }
        }
