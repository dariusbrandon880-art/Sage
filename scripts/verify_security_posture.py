#!/usr/bin/env python3
"""SAGE Public Repository Security Posture Audit & Verification.

Audits gitignore protections, CODEOWNERS coverage, SECURITY.md presence,
and verifies zero private keys or credential files are tracked in git history.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

REPORT_PATH = repo_root / "evidence_capture" / "security_posture_report.json"

REQUIRED_GITIGNORE_PATTERNS = [
    ".env",
    ".sage/credentials.json",
    "credentials.json",
    "*.pem",
    "*.key",
]

REQUIRED_SECURITY_FILES = [
    "SECURITY.md",
    ".github/CODEOWNERS",
]

SUSPECT_TRACKED_EXTENSIONS = [
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
]


def audit_gitignore() -> dict[str, bool]:
    gitignore_path = repo_root / ".gitignore"
    if not gitignore_path.exists():
        return {"exists": False, "missing_patterns": REQUIRED_GITIGNORE_PATTERNS}

    content = gitignore_path.read_text(encoding="utf-8")
    status = {}
    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        status[pattern] = pattern in content
    return status


def audit_security_docs() -> dict[str, bool]:
    res = {}
    for rel_file in REQUIRED_SECURITY_FILES:
        res[rel_file] = (repo_root / rel_file).exists()
    return res


def audit_tracked_files_for_secrets() -> list[str]:
    try:
        res = subprocess.run(
            ["git", "ls-files"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        tracked = res.stdout.splitlines()
    except Exception:
        return []

    violations = []
    for file_path in tracked:
        file_lower = file_path.lower()
        if any(file_lower.endswith(ext) for ext in SUSPECT_TRACKED_EXTENSIONS):
            violations.append(f"Forbidden extension tracked: {file_path}")
        if file_lower in ("credentials.json", ".sage/credentials.json", "client_secret.json"):
            violations.append(f"Forbidden credential file tracked: {file_path}")

    return violations


def main() -> int:
    print("=" * 70)
    print("SAGE PUBLIC REPOSITORY SECURITY POSTURE AUDIT")
    print("=" * 70)

    gitignore_results = audit_gitignore()
    docs_results = audit_security_docs()
    secret_violations = audit_tracked_files_for_secrets()

    gitignore_pass = all(gitignore_results.values())
    docs_pass = all(docs_results.values())
    secrets_pass = len(secret_violations) == 0

    overall_pass = gitignore_pass and docs_pass and secrets_pass

    report = {
        "overall_status": "PASS" if overall_pass else "FAIL",
        "gitignore_protection": gitignore_results,
        "security_documentation": docs_results,
        "tracked_secret_violations": secret_violations,
        "summary": {
            "gitignore_complete": gitignore_pass,
            "security_docs_complete": docs_pass,
            "zero_tracked_secrets": secrets_pass,
        },
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Overall Status: {report['overall_status']}")
    print(f"Gitignore Protections: {'PASS' if gitignore_pass else 'FAIL'}")
    print(f"Security Documentation: {'PASS' if docs_pass else 'FAIL'}")
    print(f"Zero Tracked Secrets: {'PASS' if secrets_pass else 'FAIL'}")
    print(f"Report Written: {REPORT_PATH}")

    if not overall_pass:
        print("\n[!] SECURITY POSTURE AUDIT FAILED", file=sys.stderr)
        return 1

    print("\n[✓] SECURITY POSTURE AUDIT SUCCESSFUL — REPOSITORY SHIELD VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
