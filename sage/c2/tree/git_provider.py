"""Concrete Git provider for atomic, ancestry-safe trunk promotion."""

from __future__ import annotations

import subprocess
from typing import Sequence

from .promotion_engine import TargetDriftError


class SubprocessGitProvider:
    """Use Git's ref transaction primitive for compare-and-swap promotion."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: Sequence[str]) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            stderr = result.stderr.strip()
            raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
        return result.stdout.strip()

    def integrate_cas(
        self, source_sha: str, expected_target_sha: str, target_branch: str
    ) -> str:
        """Atomically fast-forward a branch iff its ref still equals expected_target_sha."""
        branch = self._run_git(["check-ref-format", "--branch", target_branch])
        if branch != target_branch:
            raise RuntimeError("Git normalized the requested target branch unexpectedly")

        # Prove the new tip preserves trunk ancestry before the CAS mutation.
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", expected_target_sha, source_sha],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if ancestry.returncode:
            raise ValueError(
                "Promotion source is not a descendant of the expected canonical target"
            )

        ref = f"refs/heads/{target_branch}"
        result = subprocess.run(
            ["git", "update-ref", ref, source_sha, expected_target_sha],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            stderr = result.stderr.strip()
            if "expected" in stderr.lower() and "is at" in stderr.lower():
                raise TargetDriftError(
                    f"CAS ref update rejected for {target_branch}: {stderr}"
                )
            raise RuntimeError(f"git update-ref failed: {stderr}")

        return self._run_git(["rev-parse", ref])

    def verify_clean_status(self) -> bool:
        """Verify that the provider's working tree has no uncommitted changes."""
        return self._run_git(["status", "--porcelain"]) == ""
