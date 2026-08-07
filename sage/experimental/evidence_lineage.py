"""Evidence Lineage Index and Validation Traceability Layer.

Strengthens traceability between SAGE capabilities, validation status,
tests, evidence artifacts, and archive promotion status.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field


class EvidenceLineageRelation(BaseModel):
    """Relationship connection to another evidence artifact."""
    target_artifact_id: str
    relationship_type: str  # e.g., "derived_from", "peer_of", "generated_with"
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceLineageItem(BaseModel):
    """High-fidelity representation of an indexed evidence artifact's lineage."""
    artifact_id: str
    file_path: str
    timestamp: Optional[str] = None
    capabilities_validated: list[str] = Field(default_factory=list)
    test_suites_referenced: list[str] = Field(default_factory=list)
    validation_status: str = "UNKNOWN"
    archive_promotion_status: str = "HYPOTHESIS"  # e.g., HYPOTHESIS, READY_FOR_PROMOTION, PROMOTED
    relationships: list[EvidenceLineageRelation] = Field(default_factory=list)
    audit_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceLineageIndex(BaseModel):
    """Unified Evidence Lineage Index compiling all validation traceability traces."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_artifacts_indexed: int = 0
    artifacts: dict[str, EvidenceLineageItem] = Field(default_factory=dict)
    capability_map: dict[str, list[str]] = Field(default_factory=dict)  # maps capability to artifact IDs


class EvidenceLineageTracker:
    """Service to automatically scan, analyze, and compile Evidence Lineages."""

    def __init__(self, evidence_dir: str = "evidence_capture"):
        self.evidence_dir = Path(evidence_dir)

    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate cryptographic SHA-256 hash of a file for audit integrity."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def parse_metadata(self, file_path: Path) -> EvidenceLineageItem:
        """Parse lineage details from an individual evidence JSON file."""
        rel_path = f"evidence_capture/{file_path.name}"
        audit_hash = self.calculate_sha256(file_path)

        # Read file contents
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            # Fallback for non-JSON or corrupted files
            return EvidenceLineageItem(
                artifact_id=file_path.stem,
                file_path=rel_path,
                validation_status="MALFORMED_JSON",
                audit_hash=audit_hash,
                metadata={"error": str(e)}
            )

        # Standard extraction hooks
        if isinstance(data, list):
            # Handle JSON list/array top-level elements cleanly
            artifact_id = file_path.stem
            timestamp = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()
            validation_status = "OPERATIONAL"
            data_str = str(data)
        else:
            # Handle JSON object top-level elements
            artifact_id = (
                data.get("report_id") or
                data.get("receipt_id") or
                data.get("compliance_pack_id") or
                data.get("evaluation_id") or
                file_path.stem
            )

            # Extract timestamp
            timestamp = data.get("timestamp")
            if isinstance(timestamp, (int, float)):
                try:
                    timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                except Exception:
                    timestamp = str(timestamp)
            elif not timestamp:
                timestamp = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()

            validation_status = data.get("status") or "VALIDATED"
            data_str = str(data)

        # Define default static mapping values based on SAGE taxonomy
        capabilities = []
        tests = []
        archive_status = "READY_FOR_PROMOTION"

        name_lower = file_path.name.lower()
        if "cognitive" in name_lower:
            capabilities = ["Phase 0 SAGE Cognitive Kernel Foundation", "Prefrontal Cortex Simulator", "Cognitive Safety Gate Checks"]
            tests = ["tests/experimental/test_cognitive_kernel.py"]
            archive_status = "PROMOTED"
        elif "guard" in name_lower:
            capabilities = ["SAGE Context Guard", "Workspace Namespace Protection", "Boundary Integrity Verification"]
            tests = ["tests/experimental/test_context_guard.py"]
            if "PROTECTION_VIOLATION_DETECTED" in data_str:
                validation_status = "PROTECTION_VIOLATION_DETECTED"
        elif "operational_feedback" in name_lower or "ccl_operational" in name_lower:
            capabilities = ["SAGE Continuity Control Loop (SAGE-CCL)", "Developer Workflow Orchestrator", "SAGE Operational Intelligence Layer (OIL)"]
            tests = ["tests/experimental/test_continuity_control.py"]
        elif "discovery" in name_lower:
            capabilities = ["SAGE Operational Intelligence Layer (OIL)", "Discovery Lane Optimization"]
            tests = ["tests/experimental/test_continuity_control.py"]
            validation_status = "OPERATIONAL"
        elif "openai_runtime" in name_lower or "chatgpt_live" in name_lower:
            capabilities = ["SAGE Production OpenAI Runtime Activation", "Live Connection Handshake Validator"]
            tests = ["tests/experimental/test_run_openai_runtime_activation.py"]
            if isinstance(data, dict):
                v_res = data.get("validation_result", {})
                if isinstance(v_res, dict):
                    validation_status = v_res.get("status") or "VALIDATED"
                else:
                    validation_status = "BLOCKED_MISSING_CREDENTIALS"
            else:
                validation_status = "BLOCKED_MISSING_CREDENTIALS"
        elif "phase_4" in name_lower or "repeatability" in name_lower or "controlled_evaluation" in name_lower:
            capabilities = ["Phase 4 Repeatability & Determinism", "State Divergence Resolution (SDR-004)"]
            if "repeatability" in name_lower:
                tests = ["tests/experimental/test_phase_4_repeatability.py"]
            else:
                tests = ["tests/experimental/test_phase_4_controlled_evaluation.py"]
        elif "sdr_004" in name_lower:
            capabilities = ["State Divergence Resolution (SDR-004)", "Conflict Detection & Alignment"]
            tests = ["tests/experimental/test_sdr_004_divergence.py"]
        elif "sdr_agm" in name_lower:
            capabilities = ["SDR-AGM Simulation", "Adversarial Stress Testing & Game-Theoretic Alignment"]
            tests = ["tests/experimental/test_sdr_agm_003.py"]
        elif "demo_launcher" in name_lower:
            capabilities = ["SAGE Demo Launcher & Scenario Replay"]
            tests = ["tests/experimental/test_demo_launcher.py"]

        # Relationships hooks
        relationships = []
        if "chatgpt_live_runtime_production_activation" in name_lower:
            relationships.append(EvidenceLineageRelation(
                target_artifact_id="openai_runtime_live_connection",
                relationship_type="peer_of",
                metadata={"reason": "Generated simultaneously during secure live handshake validator runs."}
            ))

        return EvidenceLineageItem(
            artifact_id=artifact_id,
            file_path=rel_path,
            timestamp=timestamp,
            capabilities_validated=capabilities,
            test_suites_referenced=tests,
            validation_status=validation_status,
            archive_promotion_status=archive_status,
            relationships=relationships,
            audit_hash=audit_hash,
            metadata={"file_size_bytes": file_path.stat().st_size}
        )

    def compile_index(self) -> EvidenceLineageIndex:
        """Compile index scanning all evidence artifacts on disk."""
        index = EvidenceLineageIndex()

        if not self.evidence_dir.exists():
            return index

        # Scan for JSON files, excluding the index itself
        for file_path in self.evidence_dir.glob("*.json"):
            if file_path.name == "evidence_lineage_index.json":
                continue

            try:
                item = self.parse_metadata(file_path)
                index.artifacts[item.artifact_id] = item
                index.total_artifacts_indexed += 1

                # Update capability map
                for cap in item.capabilities_validated:
                    if cap not in index.capability_map:
                        index.capability_map[cap] = []
                    if item.artifact_id not in index.capability_map[cap]:
                        index.capability_map[cap].append(item.artifact_id)
            except Exception as e:
                print(f"[-] Warning: Failed to parse lineage metadata for {file_path}: {e}")

        return index

    def generate_and_save(self) -> str:
        """Generate the lineage index and persist it to evidence_capture/evidence_lineage_index.json."""
        index = self.compile_index()
        out_path = self.evidence_dir / "evidence_lineage_index.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(index.model_dump(), f, indent=2)

        print(f"[+] Successfully generated Evidence Lineage Index with {index.total_artifacts_indexed} artifacts!")
        return str(out_path)
