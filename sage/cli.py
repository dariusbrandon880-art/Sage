"""Command Line Interface for SAGE."""

import argparse
import json
import sys

from sage.runtime import SageRuntime


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="SAGE Autonomous Continuity Runtime CLI")
    subparsers = parser.add_subparsers(dest="command", help="SAGE commands")

    obj_parser = subparsers.add_parser("objective", help="Manage SAGE current objective")
    obj_parser.add_argument("--objective", type=str, help="The new objective to set")
    task_parser = subparsers.add_parser("task", help="Manage SAGE current task")
    task_parser.add_argument("--task", type=str, help="The new task to set")
    subparsers.add_parser("status", help="Get current SAGE status")

    handoff_parser = subparsers.add_parser("handoff", help="Generate a SAGE session handoff artifact")
    handoff_parser.add_argument("--file", type=str, help="The path to save the handoff JSON file")
    restore_parser = subparsers.add_parser("restore", help="Restore SAGE session state from a handoff artifact")
    restore_parser.add_argument("--file", type=str, required=True, help="The path to the handoff JSON file to restore from")

    snapshot_parser = subparsers.add_parser("snapshot", help="Manage SAGE workspace snapshots")
    snapshot_parser.add_argument("--action", choices=["create", "list", "restore"], required=True, help="Snapshot action to perform")
    snapshot_parser.add_argument("--file", type=str, help="Handoff/Snapshot file to restore from (for restore action)")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest an external session payload using the Continuity Bridge")
    ingest_parser.add_argument("--file", type=str, required=True, help="Path to the JSON file representing the payload")
    subparsers.add_parser("reason", help="Perform reasoning over continuity databases and active context")
    subparsers.add_parser("verify", help="Run repository-side self-verification and referential integrity checks")
    subparsers.add_parser("health", help="Check SAGE runtime and component health status")
    subparsers.add_parser("diagnostics", help="Generate SAGE runtime diagnostic report")
    subparsers.add_parser("capabilities", help="Get report of SAGE platform capabilities")

    chat_parser = subparsers.add_parser("chat", help="Execute a query using ChatGPTClient and SAGE runtime continuity")
    chat_mode = chat_parser.add_mutually_exclusive_group(required=True)
    chat_mode.add_argument("--prompt", type=str, help="One-shot query prompt for ChatGPT")
    chat_mode.add_argument("--interactive", action="store_true", help="Run an interactive ChatGPT session; type exit or quit to stop")

    subparsers.add_parser("metrics", help="Show collected runtime telemetry metrics")
    audit_parser = subparsers.add_parser("audit", help="ACT-PROD cross-model audit dashboard operator interface")
    audit_parser.add_argument("--action", choices=["summary", "diagnostics", "scan"], required=True, help="Audit action to perform")
    audit_parser.add_argument("--mission-id", type=str, help="Mission ID for diagnostics action")
    audit_parser.add_argument("--archive-path", type=str, default="sage_data/archive", help="Path to SAGE Archive")

    args = parser.parse_args()
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
        print(json.dumps(runtime.get_status(), indent=2))
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
            print(f"Success: Workspace snapshot created successfully. ID: {runtime.checkpoint()}")
        elif args.action == "list":
            workspace = runtime.workspace_path
            snapshots = []
            if workspace.exists():
                for path in workspace.glob("checkpoint_*.json"):
                    snapshots.append({"snapshot_id": path.stem, "file_path": str(path), "size_bytes": path.stat().st_size})
            print(json.dumps(snapshots, indent=2))
        else:
            if not args.file:
                print("Error: --file argument is required for snapshot restore action.")
                sys.exit(1)
            if not runtime.restore_session(args.file):
                print(f"Error: Failed to restore snapshot from '{args.file}'")
                sys.exit(1)
            print(f"Success: Workspace state restored successfully from snapshot '{args.file}'")
    elif args.command == "ingest":
        try:
            from sage.models import ExternalSessionPayload
            with open(args.file, "r") as f:
                result = runtime.ingest_session_payload(ExternalSessionPayload(**json.load(f)))
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Ingestion failed: {e!s}")
            sys.exit(1)
    elif args.command == "reason":
        try:
            print(json.dumps(runtime.reason_over_continuity(), indent=2))
        except Exception as e:
            print(f"Error: Reasoning failed: {e!s}")
            sys.exit(1)
    elif args.command == "verify":
        try:
            result = runtime.verify_integrity()
            print(json.dumps(result, indent=2))
            if not result.get("is_valid", False): sys.exit(1)
        except Exception as e:
            print(f"Error: Verification failed: {e!s}")
            sys.exit(1)
    elif args.command == "health":
        try:
            from sage.runtime import check_health
            print(json.dumps(check_health(runtime), indent=2))
        except Exception as e:
            print(f"Error: Health check failed: {e!s}")
            sys.exit(1)
    elif args.command == "diagnostics":
        try:
            from sage.runtime import generate_diagnostic_report
            print(json.dumps(generate_diagnostic_report(runtime), indent=2))
        except Exception as e:
            print(f"Error: Diagnostics failed: {e!s}")
            sys.exit(1)
    elif args.command == "capabilities":
        try:
            from sage.runtime import generate_capability_report
            print(json.dumps(generate_capability_report(runtime), indent=2))
        except Exception as e:
            print(f"Error: Capability reporting failed: {e!s}")
            sys.exit(1)
    elif args.command == "chat":
        try:
            from sage.integration import AIQueryRequest, ChatGPTClient
            from sage.agent_presence import get_team_context, render_chat_identity

            # Preserve the existing ChatGPTClient constructor seam for tests and
            # alternate clients while injecting canonical C2 context when supported.
            client = ChatGPTClient(runtime)
            if hasattr(client, "c2_provider"):
                client.c2_provider = get_team_context

            if args.prompt:
                response = client.execute_query(AIQueryRequest(prompt=args.prompt))
                print(render_chat_identity())
                print(response.response_text)
            else:
                session_id = None
                while True:
                    prompt = input("sage> ").strip()
                    if prompt.lower() in {"exit", "quit"}:
                        break
                    if not prompt:
                        continue
                    response = client.execute_query(AIQueryRequest(prompt=prompt, session_id=session_id))
                    session_id = response.session_id
                    print(render_chat_identity())
                    print(response.response_text)
        except Exception as e:
            print(f"Error: Chat query failed: {e!s}")
            sys.exit(1)
    elif args.command == "metrics":
        try:
            from sage.runtime import get_metrics_collector
            print(json.dumps(get_metrics_collector().get_metrics(), indent=2))
        except Exception as e:
            print(f"Error: Metrics gathering failed: {e!s}")
            sys.exit(1)
    elif args.command == "audit":
        try:
            import importlib
            dashboard_module = importlib.import_module("sage.experimental.act.act_prod_dashboard")
            dashboard = dashboard_module.SAGEActProdDashboard(archive_path=args.archive_path)
            if args.action == "summary": result = dashboard.retrieve_operator_summary()
            elif args.action == "diagnostics":
                if not args.mission_id:
                    print("Error: --mission-id is required for diagnostics action.")
                    sys.exit(1)
                result = dashboard.retrieve_mission_diagnostics(args.mission_id)
                if result is None:
                    print(f"Error: No archived trace found for mission '{args.mission_id}'")
                    sys.exit(1)
            else: result = dashboard.handle_corrupted_archive_data()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: Audit execution failed: {e!s}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
