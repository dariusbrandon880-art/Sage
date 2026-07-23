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

    # health subcommand
    subparsers.add_parser("health", help="Check SAGE runtime and component health status")

    # diagnostics subcommand
    subparsers.add_parser("diagnostics", help="Generate SAGE runtime diagnostic report")

    # capabilities subcommand
    subparsers.add_parser("capabilities", help="Get report of SAGE platform capabilities")

    # metrics subcommand
    subparsers.add_parser("metrics", help="Show collected runtime telemetry metrics")

    # command-center subcommand
    cmd_parser = subparsers.add_parser(
        "command-center", help="Launch SAGE Command Center operational visibility dashboard"
    )
    cmd_parser.add_argument("--json", action="store_true", help="Print raw JSON visibility payload")

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

    elif args.command == "health":
        try:
            from sage.runtime import check_health

            result = check_health(runtime)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Health check failed: {str(e)}")
            sys.exit(1)

    elif args.command == "diagnostics":
        try:
            from sage.runtime import generate_diagnostic_report

            result = generate_diagnostic_report(runtime)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Diagnostics failed: {str(e)}")
            sys.exit(1)

    elif args.command == "capabilities":
        try:
            from sage.runtime import generate_capability_report

            result = generate_capability_report(runtime)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Capability reporting failed: {str(e)}")
            sys.exit(1)

    elif args.command == "metrics":
        try:
            from sage.runtime import get_metrics_collector

            result = get_metrics_collector().get_metrics()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Metrics gathering failed: {str(e)}")
            sys.exit(1)

    elif args.command == "command-center":
        try:
            from sage.command_center import CommandCenter

            cmd_center = CommandCenter(runtime)
            payload = cmd_center.get_visibility_payload()

            if args.json:
                print(json.dumps(payload, indent=2))
            else:
                # Beautiful, styled terminal dashboard for SAGE Command Center v1
                GREEN = "\033[92m"
                YELLOW = "\033[93m"
                RED = "\033[91m"
                CYAN = "\033[96m"
                BOLD = "\033[1m"
                RESET = "\033[0m"

                sys_view = payload["current_system_view"]
                arch_view = payload["archive_view"]
                rt_view = payload["runtime_view"]
                cont_view = payload["continuity_view"]

                print("=" * 70)
                print(
                    f"{BOLD}{GREEN}      SAGE COMMAND CENTER v1 - OPERATIONAL VISIBILITY INTERFACE{RESET}"
                )
                print("=" * 70)
                print(f"Timestamp: {payload['timestamp']}")
                print("-" * 70)

                # 1. Current System View
                status_color = GREEN if sys_view["runtime_status"] == "active" else RED
                print(f"{BOLD}{CYAN}[1. CURRENT SYSTEM VIEW]{RESET}")
                print(
                    f"  Runtime Status  : {status_color}{sys_view['runtime_status'].upper()}{RESET}"
                )
                print(f"  Milestone       : {YELLOW}{sys_view['current_milestone']}{RESET}")
                print(f"  Active Task     : {sys_view['active_task']}")
                print(f"  Blockers        : {sys_view['blockers'] or 'None'}")
                print(f"  Last Checkpoint : {sys_view['last_checkpoint']}")
                val_color = GREEN if sys_view["validation_state"].get("is_valid") else RED
                print(
                    f"  Validation State: {val_color}{'VALID' if sys_view['validation_state'].get('is_valid') else 'INVALID'}{RESET}"
                )
                print("-" * 70)

                # 2. Archive View
                print(f"{BOLD}{CYAN}[2. ARCHIVE VIEW]{RESET}")
                print(
                    f"  Master Archive Status: {GREEN}{arch_view['master_archive_status'].upper()}{RESET}"
                )
                print(f"  Latest Reports Count : {len(arch_view['latest_reports'])}")
                print(f"  Recent Decisions     : {len(arch_view['recent_decisions'])} recorded")
                print(
                    f"  Recent Archive Logs  : {len(arch_view['recent_operational_records'])} logged"
                )
                print("-" * 70)

                # 3. Runtime View
                print(f"{BOLD}{CYAN}[3. RUNTIME VIEW]{RESET}")
                h_color = (
                    GREEN
                    if rt_view["health_status"]["status"] == "healthy"
                    else (YELLOW if rt_view["health_status"]["status"] == "degraded" else RED)
                )
                print(
                    f"  Health Status        : {h_color}{rt_view['health_status']['status'].upper()}{RESET}"
                )
                print(f"  API Port             : {rt_view['api_status']['port']}")
                print("  Active Connectors    :")
                for provider, state in rt_view["active_connectors"].items():
                    c_color = GREEN if state == "CONNECTED" else RED
                    print(f"    - {provider:<20}: {c_color}{state}{RESET}")
                print("-" * 70)

                # 4. Continuity View
                print(f"{BOLD}{CYAN}[4. CONTINUITY VIEW]{RESET}")
                print(
                    f"  Lineage Objective    : {cont_view['latest_session_state'].get('current_objective') or 'None'}"
                )
                print(
                    f"  Checkpoint History   : {len(cont_view['checkpoint_history'])} checkpoints available"
                )
                ready_color = GREEN if cont_view["restoration_readiness"]["can_restore"] else YELLOW
                print(
                    f"  Restoration Readiness: {ready_color}{'READY' if cont_view['restoration_readiness']['can_restore'] else 'MOCK READY (NO CHECKPOINTS)'}{RESET}"
                )
                print("=" * 70)

        except Exception as e:
            print(f"Error: Command Center failed: {str(e)}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
