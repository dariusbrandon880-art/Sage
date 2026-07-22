"""Command Line Interface for SAGE."""

import argparse
import sys
import json
from sage.runtime import SageRuntime


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="SAGE Autonomous Continuity Runtime CLI")
    subparsers = parser.add_subparsers(dest="command", help="SAGE commands")

    # objective subcommand
    obj_parser = subparsers.add_parser("objective", help="Manage SAGE current objective")
    obj_parser.add_argument("--objective", type=str, help="The new objective to set")

    # task subcommand
    task_parser = subparsers.add_parser("task", help="Manage SAGE current task")
    task_parser.add_argument("--task", type=str, help="The new task to set")

    # status subcommand
    subparsers.add_parser("status", help="Get current SAGE status")

    # handoff subcommand
    handoff_parser = subparsers.add_parser(
        "handoff", help="Generate a SAGE session handoff artifact"
    )
    handoff_parser.add_argument("--file", type=str, help="The path to save the handoff JSON file")

    # restore subcommand
    restore_parser = subparsers.add_parser(
        "restore", help="Restore SAGE session state from a handoff artifact"
    )
    restore_parser.add_argument(
        "--file", type=str, required=True, help="The path to the handoff JSON file to restore from"
    )

    # snapshot subcommand
    snapshot_parser = subparsers.add_parser("snapshot", help="Manage SAGE workspace snapshots")
    snapshot_parser.add_argument(
        "--action",
        choices=["create", "list", "restore"],
        required=True,
        help="Snapshot action to perform",
    )
    snapshot_parser.add_argument(
        "--file", type=str, help="Handoff/Snapshot file to restore from (for restore action)"
    )

    # ingest subcommand
    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest an external session payload using the Continuity Bridge"
    )
    ingest_parser.add_argument(
        "--file", type=str, required=True, help="Path to the JSON file representing the payload"
    )

    # reason subcommand
    subparsers.add_parser(
        "reason", help="Perform reasoning over continuity databases and active context"
    )

    # verify subcommand
    subparsers.add_parser(
        "verify", help="Run repository-side self-verification and referential integrity checks"
    )

    # auto-capture subcommand
    subparsers.add_parser(
        "auto-capture",
        help="Automatically capture the local git workspace & ADR context and ingest it",
    )

    args = parser.parse_args()

    # Initialize runtime
    runtime = SageRuntime()

    if args.command == "objective":
        if args.objective:
            session_id = runtime.set_objective(args.objective)
            print(f"Success: Objective set to '{args.objective}'")
            print(f"Session ID: {session_id}")
        else:
            print(f"Current Objective: {runtime.current_state.current_objective or 'None'}")

    elif args.command == "task":
        if args.task:
            session_id = runtime.set_task(args.task)
            print(f"Success: Task set to '{args.task}'")
            print(f"Session ID: {session_id}")
        else:
            print(f"Current Task: {runtime.current_state.active_task or 'None'}")

    elif args.command == "status":
        status = runtime.get_status()
        print(json.dumps(status, indent=2))

    elif args.command == "handoff":
        path = runtime.generate_handoff(args.file)
        print(f"Success: Handoff generated successfully at: '{path}'")

    elif args.command == "restore":
        success = runtime.restore_session(args.file)
        if success:
            print(f"Success: SAGE session state restored successfully from '{args.file}'")
            print(f"Current Objective: {runtime.current_state.current_objective or 'None'}")
            print(f"Current Task: {runtime.current_state.active_task or 'None'}")
        else:
            print(f"Error: Failed to restore session from '{args.file}'")
            sys.exit(1)

    elif args.command == "snapshot":
        if args.action == "create":
            snapshot_id = runtime.checkpoint()
            print(f"Success: Workspace snapshot created successfully. ID: {snapshot_id}")
        elif args.action == "list":
            workspace = runtime.workspace_path
            snapshots = []
            if workspace.exists():
                for path in workspace.glob("checkpoint_*.json"):
                    snapshots.append(
                        {
                            "snapshot_id": path.stem,
                            "file_path": str(path),
                            "size_bytes": path.stat().st_size,
                        }
                    )
            print(json.dumps(snapshots, indent=2))
        elif args.action == "restore":
            if not args.file:
                print("Error: --file argument is required for snapshot restore action.")
                sys.exit(1)
            success = runtime.restore_session(args.file)
            if success:
                print(f"Success: Workspace state restored successfully from snapshot '{args.file}'")
            else:
                print(f"Error: Failed to restore snapshot from '{args.file}'")
                sys.exit(1)

    elif args.command == "ingest":
        try:
            with open(args.file, "r") as f:
                payload_data = json.load(f)
            from sage.models import ExternalSessionPayload

            payload = ExternalSessionPayload(**payload_data)
            result = runtime.ingest_session_payload(payload)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Ingestion failed: {str(e)}")
            sys.exit(1)

    elif args.command == "reason":
        try:
            result = runtime.reason_over_continuity()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Reasoning failed: {str(e)}")
            sys.exit(1)

    elif args.command == "verify":
        try:
            result = runtime.verify_integrity()
            print(json.dumps(result, indent=2))
            if not result.get("is_valid", False):
                sys.exit(1)
        except Exception as e:
            print(f"Error: Verification failed: {str(e)}")
            sys.exit(1)

    elif args.command == "auto-capture":
        try:
            result = runtime.auto_capture_git_session()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Automated capture failed: {str(e)}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
