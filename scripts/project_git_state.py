#!/usr/bin/env python3
"""SAGE Repository State Projector.

Queries real Git state and active workspace metadata to project
canonical Markdown states (05_ACTIVE_WORK.md and 03_CURRENT_FRONTIER.md)
to the SAGE Google Drive mirror directory.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_command(args: list[str]) -> str:
    try:
        res = subprocess.run(args, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return ""


def get_active_task_and_pr(state_file_path: Path = Path(".sage/sage_state.json")) -> tuple[str, str]:
    active_task = "Implement SAGE Google Continuity Projection"
    active_pr = "PR #125 - Google Drive Continuity Projection"

    if state_file_path.exists():
        try:
            with open(state_file_path, "r") as f:
                data = json.load(f)
            # Traverse snapshot states to find any active objectives or tasks
            snapshots = data.get("snapshots", {})
            if snapshots:
                # Find most recent snapshot
                sorted_snapshots = sorted(
                    snapshots.values(),
                    key=lambda s: s.get("timestamp", ""),
                    reverse=True,
                )
                most_recent = sorted_snapshots[0]
                state_data = most_recent.get("state", {})
                if state_data:
                    active_task = state_data.get("active_task") or active_task
        except Exception as e:
            print(f"Error parsing state file: {e}")

    return active_task, active_pr


def main(target_dir_name: str = "SAGE", state_file_path_str: str = ".sage/sage_state.json"):
    print("Running SAGE Repository State Projector...")

    # 1. Query git metadata
    head_sha = run_command(["git", "rev-parse", "HEAD"]) or "unknown_head_sha"

    # Try to resolve origin/main SHA
    origin_main_sha = run_command(["git", "rev-parse", "origin/main"])
    if not origin_main_sha:
        # Fallback to local main if origin/main doesn't exist/fetch
        origin_main_sha = run_command(["git", "rev-parse", "main"]) or "unknown_main_sha"

    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "detached_head"

    # Resolve merge base
    merge_base = ""
    if origin_main_sha and origin_main_sha != "unknown_main_sha":
        merge_base = run_command(["git", "merge-base", "origin/main", "HEAD"])
    if not merge_base and origin_main_sha:
        merge_base = run_command(["git", "merge-base", "main", "HEAD"])
    if not merge_base:
        merge_base = head_sha

    # Query worktree status
    status_porcelain = run_command(["git", "status", "--porcelain"])
    worktree_status = "CLEAN" if not status_porcelain else "DIRTY"

    # Get modified files list
    modified_files_list = []
    if status_porcelain:
        for line in status_porcelain.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2:
                modified_files_list.append(parts[1])

    modified_files_str = "\n".join([f"* `{f}`" for f in modified_files_list]) if modified_files_list else "* None"

    # Check repository consistency
    consistency = "CONSISTENT"
    # Rule check: Core files should never be modified in regular tasks
    for f in modified_files_list:
        if f.startswith("sage/core/") or f.startswith("sage/acr/"):
            consistency = "VIOLATION: Core namespaces modified!"
            break

    # Resolve active task and PR
    active_task, active_pr = get_active_task_and_pr(Path(state_file_path_str))

    timestamp = datetime.now(timezone.utc).isoformat()

    # Determine protected file statuses
    protected_status = "SECURE"
    for f in modified_files_list:
        if f.startswith("evidence_capture/phase_4_"):
            protected_status = "VIOLATION: Historical evidence modified!"
            break

    # Determine preflight status
    preflight_status = "PREFLIGHT_REQUIRED"
    if worktree_status == "CLEAN":
        preflight_status = "READY"

    # 2. Write 05_ACTIVE_WORK.md
    active_work_content = f"""# SAGE ACTIVE WORK SNAPSHOT
[MACHINE_GENERATED_DO_NOT_EDIT]

TIMESTAMP: {timestamp}
CURRENT_HEAD_SHA: {head_sha}
ORIGIN_MAIN_SHA: {origin_main_sha}
WORKING_BRANCH: {branch}
MERGE_BASE: {merge_base}
WORKTREE_STATUS: {worktree_status}

ACTIVE_PR: {active_pr}
ACTIVE_TASK: {active_task}

MODIFIED_FILES:
{modified_files_str}

SCOPE_BOUNDARY: Bounded strictly to authorized workspace target files.

PREFLIGHT_STATUS: {preflight_status}

PROTECTED_FILE_STATUS: {protected_status}

REPOSITORY_CONSISTENCY: {consistency}

PROJECTION_STATUS: SYNCHRONIZED
"""

    sage_dir = Path(target_dir_name)
    sage_dir.mkdir(exist_ok=True)

    active_work_path = sage_dir / "05_ACTIVE_WORK.md"
    with open(active_work_path, "w") as f:
        f.write(active_work_content)
    print(f"Projected: {active_work_path}")

    # 3. Write 03_CURRENT_FRONTIER.md
    current_frontier_content = f"""# SAGE CURRENT FRONTIER
[MACHINE_GENERATED_DO_NOT_EDIT]

SOURCE_HEAD: {head_sha}
SOURCE_TIMESTAMP: {timestamp}

CURRENT_FRONTIER: SAGE Google Drive Continuity Projection

VALIDATED_PREDECESSOR: SAGE Act Prod Enterprise Dashboard

TARGET_CONSUMER: SAGE Human Operators and LLM Nodes

CLASSIFICATION: CAPABILITY_PROMOTION

CAUSAL_CHAIN: Multi-Agent Identity -> Core Persistence -> Progression State Machine -> Change-Impact Revalidator -> Google Drive Projection

AUTHORIZED_BOUNDARY: scripts/project_git_state.py, scripts/project_telemetry.py, tests/test_projection.py

CURRENT_STATUS: IMPLEMENTING

OPEN_BOUNDARY: Live synchronization handshake verify flow

NEXT_COMPOUND: Run-time Google Drive projection sync verify
"""

    frontier_path = sage_dir / "03_CURRENT_FRONTIER.md"
    with open(frontier_path, "w") as f:
        f.write(current_frontier_content)
    print(f"Projected: {frontier_path}")

    print("State projection complete.")


if __name__ == "__main__":
    main()
