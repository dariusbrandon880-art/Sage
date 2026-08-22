#!/usr/bin/env python3
"""Dispatch the canonical SAGE five-flight workflow through GitHub Actions.

This is an execution adapter, not an intelligence/evaluation layer. It requires
an explicit GitHub token with Actions: write permission and refuses to dispatch
anything other than the canonical five-flight workflow/ref.
"""
from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request

OWNER = "dariusbrandon880-art"
REPO = "Sage"
WORKFLOW = "main.yml"
REF = "main"
EXPECTED_FLIGHTS = ("003", "004", "005", "006", "007")


def dispatch(token: str) -> None:
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW}/dispatches"
    payload = b'{"ref":"main"}'
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2026-03-10",
            "Content-Type": "application/json",
            "User-Agent": "SAGE-governed-five-flight-dispatch",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 204:
                raise RuntimeError(f"unexpected GitHub status: {response.status}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub dispatch failed: HTTP {exc.code}: {body}") from exc


def main() -> int:
    token = os.environ.get("SAGE_GITHUB_ACTIONS_TOKEN")
    if not token:
        print("BLOCKED: SAGE_GITHUB_ACTIONS_TOKEN is required", file=sys.stderr)
        return 2
    print("SAGE governed wave: 003,004,005,006,007")
    print("workflow: main.yml")
    print("ref: main")
    dispatch(token)
    print("DISPATCH_ACCEPTED: GitHub Actions accepted the five-flight workflow request")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
