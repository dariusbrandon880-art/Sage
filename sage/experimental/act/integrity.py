"""SAGE Experimental Evidence Integrity Validation Utility."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class EvidenceIntegrityVerifier:
    """Computes, registers, and verifies SHA-256 cryptographic digests of sandbox evidence."""

    @staticmethod
    def compute_sha256(filepath: Path) -> str:
        """Computes the SHA-256 checksum of a file.

        Args:
            filepath: Path to the target file.

        Returns:
            The hex digest string.
        """
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def generate_manifest(self, filepaths: List[Path]) -> Dict[str, Any]:
        """Generates an integrity manifest dictionary for a list of file paths.

        Does not modify existing evidence files on disk. Only computes digests.
        """
        integrity_results = {}
        for path in filepaths:
            if not path.exists():
                raise FileNotFoundError(f"Integrity Violation: Targeted evidence file '{path}' does not exist.")
            integrity_results[str(path)] = self.compute_sha256(path)

        return {
            "verified_evidence_files": [str(p) for p in filepaths],
            "integrity_results": integrity_results,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            "validation_status": "INTEGRITY_VERIFIED",
            "human_review_state": "HUMAN_APPROVAL_REQUIRED",
        }

    def verify_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Verifies files listed inside a manifest against their current active disk digests.

        Enforces strict fail-closed behavior on edit, mismatch, or deletion.
        """
        results = {"status": "SUCCESS", "mismatches": [], "missing": []}
        recorded_results = manifest.get("integrity_results", {})

        for path_str, recorded_digest in recorded_results.items():
            path = Path(path_str)
            if not path.exists():
                results["status"] = "FAIL_CLOSED"
                results["missing"].append(path_str)
                continue

            current_digest = self.compute_sha256(path)
            if current_digest != recorded_digest:
                results["status"] = "FAIL_CLOSED"
                results["mismatches"].append({
                    "file": path_str,
                    "expected": recorded_digest,
                    "actual": current_digest,
                })

        return results
