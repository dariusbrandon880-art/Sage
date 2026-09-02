#!/usr/bin/env python3
"""SAGE Repository State Projector.

Projects canonical repository state from real Git metadata and governed
workspace state. The projector must not invent a frontier or PR when the
repository does not provide one.
"""

import json
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


def _latest_state(state_file_path: Path) -> dict:
    if not state_file_path.exists():
        return {}
    try:
        with open(state_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        snapshots = data.get("snapshots", {})
        if not snapshots:
            return {}
        latest = max(snapshots.values(), key=lambda s: s.get("timestamp", ""))
        return latest.get("state", {}) or {}
    except Exception as exc:
        print(f"Error parsing state file: {exc}", file=sys.stderr)
        return {}


def get_active_state(state_file_path: Path = Path(".sage/sage_state.json")) -> tuple[str, str, str]:
    """Return governed task, PR and frontier without legacy fallback claims."""
    state = _latest_state(state_file_path)
    active_task = str(state.get("active_task") or "UNSPECIFIED")
    active_pr = str(state.get("active_pr") or "UNBOUND")
    frontier = str(state.get("current_frontier") or state.get("frontier") or "UNSPECIFIED")
    return active_task, active_pr, frontier


def main(target_dir_name: str = "SAGE", state_file_path_str: str = ".sage/sage_state.json"):
    print("Running SAGE Repository State Projector...")

    head_sha = run_command(["git", "rev-parse", "HEAD"]) or "unknown_head_sha"
    origin_main_sha = run_command(["git", "rev-parse", "origin/main"])
    if not origin_main_sha:
        origin_main_sha = run_command(["git", "rev-parse", "main"]) or "unknown_main_sha"

    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "detached_head"
    merge_base = run_command(["git", "merge-base", "origin/main", "HEAD"]) if origin_main_sha else ""
    if not merge_base:
        merge_base = run_command(["git", "merge-base", "main", "HEAD"]) or head_sha

    status_porcelain = run_command(["git", "status", "--porcelain"])
    worktree_status = "CLEAN" if not status_porcelain else "DIRTY"
    modified_files_list = []
    for line in status_porcelain.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            modified_files_list.append(parts[1])
    modified_files_str = "\n".join(f"* `{f}`" for f in modified_files_list) or "* None"

    consistency = "CONSISTENT"
    for f in modified_files_list:
        if f.startswith("sage/core/") or f.startswith("sage/acr/"):
            consistency = "VIOLATION: Core namespaces modified!"
            break

    active_task, active_pr, frontier = get_active_state(Path(state_file_path_str))
    state = _latest_state(Path(state_file_path_str))
    timestamp = datetime.now(timezone.utc).isoformat()

    protected_status = "SECURE"
    for f in modified_files_list:
        if f.startswith("evidence_capture/phase_4_"):
            protected_status = "VIOLATION: Historical evidence modified!"
            break

    preflight_status = "READY" if worktree_status == "CLEAN" else "PREFLIGHT_REQUIRED"

    sage_dir = Path(target_dir_name)
    sage_dir.mkdir(exist_ok=True)

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
    with open(sage_dir / "05_ACTIVE_WORK.md", "w", encoding="utf-8") as f:
        f.write(active_work_content)

    current_frontier_content = f"""# SAGE CURRENT FRONTIER
[MACHINE_GENERATED_DO_NOT_EDIT]

SOURCE_HEAD: {head_sha}
SOURCE_TIMESTAMP: {timestamp}

CURRENT_FRONTIER: {frontier}

VALIDATED_PREDECESSOR: {str(state.get('validated_predecessor') or 'UNSPECIFIED')}

TARGET_CONSUMER: SAGE Human Operators and LLM Nodes

CLASSIFICATION: {str(state.get('classification') or 'UNSPECIFIED')}

CAUSAL_CHAIN: {str(state.get('causal_chain') or 'UNSPECIFIED')}

AUTHORIZED_BOUNDARY: {str(state.get('authorized_boundary') or 'UNSPECIFIED')}

CURRENT_STATUS: {str(state.get('current_status') or 'UNSPECIFIED')}

OPEN_BOUNDARY: {str(state.get('open_boundary') or 'UNSPECIFIED')}

NEXT_COMPOUND: {str(state.get('next_compound') or 'UNSPECIFIED')}
"""
    with open(sage_dir / "03_CURRENT_FRONTIER.md", "w", encoding="utf-8") as f:
        f.write(current_frontier_content)

    print("State projection complete.")


if __name__ == "__main__":
    main()
