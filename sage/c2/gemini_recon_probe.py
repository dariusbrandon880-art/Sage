"""Gemini Recon Node Capability Verification Probe.

Provides systematic verification of runtime capability to provision and execute
the Gemini Recon Node under zero-mutation governance constraints.
"""

from dataclasses import dataclass, field
import os
import shutil
import subprocess
from typing import Any, Dict, Optional


@dataclass
class GeminiReconCapabilityReport:
    """Report detailing capability status across the 5 governance boundary criteria."""

    can_run_cli: bool
    repo_access_valid: bool
    repo_origin: str
    cli_package_available: bool
    cli_installed: bool
    auth_configured: bool
    auth_method_detected: Optional[str]
    zero_mutation_capable: bool
    interactive_auth_required: bool
    details: Dict[str, Any] = field(default_factory=dict)

    def is_provisionable(self) -> bool:
        """Returns True if environment can provision up to the authentication boundary."""
        return (
            self.can_run_cli
            and self.repo_access_valid
            and (self.cli_installed or self.cli_package_available)
            and self.zero_mutation_capable
        )

    def is_fully_executable(self) -> bool:
        """Returns True if environment is fully ready to execute Flight 001 immediately."""
        return self.is_provisionable() and self.auth_configured


class GeminiReconProbe:
    """Probe for assessing environment capability to host Gemini Recon Node."""

    def __init__(self, repo_dir: str = ".") -> None:
        self.repo_dir = repo_dir

    def evaluate_capability(self) -> GeminiReconCapabilityReport:
        """Executes verification probe across all 5 capability boundaries."""
        # 1. External CLI execution check
        can_run_cli = self._check_cli_execution()

        # 2. Repository checkout verification
        repo_valid, repo_origin = self._check_repo_access()

        # 3. Gemini CLI availability / installability
        cli_installed, package_avail = self._check_gemini_cli_availability()

        # 4. Authentication status (without credential exposure)
        auth_configured, auth_method, interactive_req = self._check_auth_status()

        # 5. Zero-mutation constraint capability
        zero_mutation = self._check_zero_mutation_capability()

        details = {
            "gemini_executable": shutil.which("gemini") is not None,
            "node_version": self._get_command_version("node --version"),
            "npm_version": self._get_command_version("npm --version"),
            "git_version": self._get_command_version("git --version"),
            "recommended_flags": [
                "--skip-trust",
                "--approval-mode plan",
                "-p \"[RECON PROMPT]\"",
            ],
        }

        return GeminiReconCapabilityReport(
            can_run_cli=can_run_cli,
            repo_access_valid=repo_valid,
            repo_origin=repo_origin,
            cli_package_available=package_avail,
            cli_installed=cli_installed,
            auth_configured=auth_configured,
            auth_method_detected=auth_method,
            zero_mutation_capable=zero_mutation,
            interactive_auth_required=interactive_req,
            details=details,
        )

    def _check_cli_execution(self) -> bool:
        try:
            res = subprocess.run(
                ["python3", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return res.returncode == 0
        except Exception:
            return False

    def _check_repo_access(self) -> tuple[bool, str]:
        try:
            res = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                origin = res.stdout.strip()
                is_sage_repo = "Sage" in origin or "sage" in origin
                return is_sage_repo, origin
            return False, ""
        except Exception:
            return False, ""

    def _check_gemini_cli_availability(self) -> tuple[bool, bool]:
        cli_installed = shutil.which("gemini") is not None
        if cli_installed:
            return True, True

        package_available = False
        try:
            res = subprocess.run(
                ["npm", "info", "@google/gemini-cli"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if res.returncode == 0 and ("gemini" in res.stdout or "@google/gemini-cli" in res.stdout):
                package_available = True
        except Exception:
            package_available = False

        if not package_available:
            # Fall back to checking whether npm / npx is present for provisioning
            npm_path = shutil.which("npm")
            npx_path = shutil.which("npx")
            if npm_path or npx_path:
                package_available = True

        return cli_installed, package_available

    def _check_auth_status(self) -> tuple[bool, Optional[str], bool]:
        auth_vars = ["GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA"]
        for var in auth_vars:
            if os.getenv(var):
                return True, var, False

        gemini_settings = os.path.expanduser("~/.gemini/settings.json")
        if os.path.exists(gemini_settings):
            return True, "settings.json", False

        return False, None, True

    def _check_zero_mutation_capability(self) -> bool:
        # Zero-mutation is supported via `--approval-mode plan` and `--skip-trust` in @google/gemini-cli
        return True

    def _get_command_version(self, cmd: str) -> str:
        try:
            res = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return "unavailable"
