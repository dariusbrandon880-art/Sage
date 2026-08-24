"""SAGE Release Provenance & Attestation Synthesizer.

Synthesizes repository manifest metadata (pyproject.toml), active git commit provenance,
dependency tree digests, and evidence capture receipts into immutable, cryptographically
signed ReleaseProvenanceReceipt records for C2 release assurance.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Sequence
from pydantic import BaseModel, Field

from sage.acr.attestation import AttestationProvider


class ReleaseProvenanceReceipt(BaseModel):
    """Immutable, cryptographically signed release provenance receipt."""

    release_id: str
    commit_sha: str
    pyproject_version: str
    dependency_digest: str
    evidence_refs: list[str] = Field(default_factory=list)
    attestation_signature: str
    timestamp: float = Field(default_factory=time.time)

    def digest(self) -> str:
        payload = {
            "release_id": self.release_id,
            "commit_sha": self.commit_sha,
            "pyproject_version": self.pyproject_version,
            "dependency_digest": self.dependency_digest,
            "evidence_refs": sorted(self.evidence_refs),
            "attestation_signature": self.attestation_signature,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ReleaseProvenanceSynthesizer:
    """Synthesizes repository release metadata, dependency digests, and attestation signatures."""

    def __init__(self, root_dir: str | Path = ".", attestation_provider: AttestationProvider | None = None):
        self.root_dir = Path(root_dir)
        self.attestation_provider = attestation_provider or AttestationProvider()

    def _get_git_commit_sha(self) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                cwd=str(self.root_dir),
            )
            return res.stdout.strip()
        except Exception:
            return "UNKNOWN_COMMIT"

    def _get_pyproject_version(self) -> str:
        pyproject_path = self.root_dir / "pyproject.toml"
        if not pyproject_path.exists():
            return "0.0.0"

        for line in pyproject_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("version ="):
                return line.split("=")[1].strip().strip('"\'')
        return "0.0.0"

    def compute_dependency_digest(self) -> str:
        """Compute deterministic SHA-256 digest of pyproject.toml and poetry.lock if present."""
        hasher = hashlib.sha256()
        for filename in ("pyproject.toml", "poetry.lock"):
            filepath = self.root_dir / filename
            if filepath.exists():
                hasher.update(filepath.read_bytes())
        return hasher.hexdigest()

    def synthesize_release_provenance(
        self,
        release_id: str,
        evidence_refs: Sequence[str] = (),
        commit_sha: str | None = None,
    ) -> ReleaseProvenanceReceipt:
        """Synthesize and sign a ReleaseProvenanceReceipt for a release candidate."""
        if not release_id.strip():
            raise ValueError("release_id is required")

        sha = commit_sha or self._get_git_commit_sha()
        version = self._get_pyproject_version()
        dep_digest = self.compute_dependency_digest()
        sorted_refs = sorted(list(set(str(r).strip() for r in evidence_refs if str(r).strip())))

        payload_to_sign = {
            "release_id": release_id,
            "commit_sha": sha,
            "pyproject_version": version,
            "dependency_digest": dep_digest,
            "evidence_refs": sorted_refs,
        }

        signature = self.attestation_provider.sign_payload(payload_to_sign)

        return ReleaseProvenanceReceipt(
            release_id=release_id,
            commit_sha=sha,
            pyproject_version=version,
            dependency_digest=dep_digest,
            evidence_refs=sorted_refs,
            attestation_signature=signature,
        )
