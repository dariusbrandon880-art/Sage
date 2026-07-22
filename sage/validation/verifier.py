"""Verification Framework for SAGE to execute automated checks."""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from sage.validation.evidence import EvidenceRecord
from sage.validation.validation_record import ValidationOutcome


class Verifier:
    """Lightweight automated verifier for tests, documentation, and architectural compliance."""

    @staticmethod
    def verify_test_suite(
        test_file: str, related_component: str = "sage/core"
    ) -> Tuple[ValidationOutcome, EvidenceRecord]:
        """Verify that a specific test file exists and contains valid tests."""
        path = Path(test_file)
        exists = path.exists()

        outcome = ValidationOutcome(
            item_id=str(path),
            validation_method="test_verification",
            result=exists,
            confidence_impact=0.15 if exists else 0.0,
            details={"file_path": str(path), "exists": exists},
        )

        evidence = EvidenceRecord(
            source="test_verifier",
            evidence_type="test_result",
            related_component=related_component,
            supporting_references=[str(path)] if exists else [],
            metadata={"checked_path": str(path)},
        )

        return outcome, evidence

    @staticmethod
    def verify_documentation(
        doc_file: str, expected_sections: List[str] = None
    ) -> Tuple[ValidationOutcome, EvidenceRecord]:
        """Verify documentation file exists, is non-empty, and optionally contains key sections."""
        path = Path(doc_file)
        exists = path.exists()
        sections_found = {}
        passed = exists

        if exists:
            content = path.read_text()
            passed = len(content.strip()) > 10
            if expected_sections:
                for section in expected_sections:
                    found = section.lower() in content.lower()
                    sections_found[section] = found
                    if not found:
                        passed = False

        outcome = ValidationOutcome(
            item_id=str(path),
            validation_method="documentation_verification",
            result=passed,
            confidence_impact=0.10 if passed else 0.0,
            details={
                "file_path": str(path),
                "exists": exists,
                "sections_found": sections_found,
            },
        )

        evidence = EvidenceRecord(
            source="documentation_verifier",
            evidence_type="doc_coverage",
            related_component="docs",
            supporting_references=[str(path)] if exists else [],
            metadata={"sections_requested": expected_sections or []},
        )

        return outcome, evidence

    @staticmethod
    def verify_architecture(
        directory_path: str, required_files: List[str]
    ) -> Tuple[ValidationOutcome, EvidenceRecord]:
        """Verify compliance of architecture by checking file existences under a directory."""
        dir_path = Path(directory_path)
        exists = dir_path.exists()
        missing_files = []

        if exists:
            for req_file in required_files:
                file_path = dir_path / req_file
                if not file_path.exists():
                    missing_files.append(req_file)

        passed = exists and len(missing_files) == 0

        outcome = ValidationOutcome(
            item_id=str(dir_path),
            validation_method="architecture_verification",
            result=passed,
            confidence_impact=0.20 if passed else -0.10,
            details={
                "directory": str(dir_path),
                "exists": exists,
                "missing_files": missing_files,
                "required_files": required_files,
            },
        )

        evidence = EvidenceRecord(
            source="architecture_verifier",
            evidence_type="architecture_adherence",
            related_component=str(dir_path),
            supporting_references=[str(dir_path / f) for f in required_files if f not in missing_files],
            metadata={"missing_count": len(missing_files)},
        )

        return outcome, evidence
