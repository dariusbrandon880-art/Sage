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
    handoff_parser = subparsers.add_parser("handoff", help="Generate a SAGE session handoff artifact")
    handoff_parser.add_argument("--file", type=str, help="The path to save the handoff JSON file")

    # restore subcommand
    restore_parser = subparsers.add_parser("restore", help="Restore SAGE session state from a handoff artifact")
    restore_parser.add_argument("--file", type=str, required=True, help="The path to the handoff JSON file to restore from")

    # snapshot subcommand
    snapshot_parser = subparsers.add_parser("snapshot", help="Manage workspace snapshots")
    snapshot_subparsers = snapshot_parser.add_subparsers(dest="action", help="Snapshot actions")

    # snapshot create
    snapshot_subparsers.add_parser("create", help="Create a new workspace snapshot")

    # snapshot list
    snapshot_subparsers.add_parser("list", help="List all workspace snapshots")

    # snapshot restore [id]
    snapshot_restore_parser = snapshot_subparsers.add_parser("restore", help="Restore workspace state from a snapshot")
    snapshot_restore_parser.add_argument("id", type=str, help="The ID of the snapshot to restore")

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
            snapshot_id = runtime.create_workspace_snapshot()
            print(f"Success: Snapshot created successfully with ID: '{snapshot_id}'")
        elif args.action == "list":
            snapshots = runtime.list_workspace_snapshots()
            if not snapshots:
                print("No snapshots found.")
            else:
                for s in snapshots:
                    print(f"- ID: {s['id']} (Created: {s['timestamp']})")
        elif args.action == "restore":
            success = runtime.restore_workspace_snapshot(args.id)
            if success:
                print(f"Success: SAGE workspace snapshot '{args.id}' restored successfully.")
            else:
                print(f"Error: Failed to restore snapshot '{args.id}'")
                sys.exit(1)
        else:
            snapshot_parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
