"""Command Line Interface for SAGE."""

import argparse
import json
import sys

from sage.runtime import SageRuntime


def _print_c2_bootstrap(runtime):
    from sage.agent_presence import render_chat_identity
    print("[SAGE::C2::CHATGPT] C2 MISSION CONTROL")
    print("MISSION LOCK: SAGE Operational Convergence")
    print("REALITY LOCK: repository state and acceptance evidence required")
    print("STATE LOCK: canonical mission contract + active work reconciled")
    print("FLIGHT BOARD: F1=FOUNDATION F2=INTELLIGENCE F3=EXECUTION F4=VERIFICATION F5=WAREHOUSE")
    print("EXECUTION LOOP: SENSE -> VERIFY -> ORIENT -> EXECUTE -> OBSERVE -> VALIDATE -> COMPOUND")
    print("ANTI-DRIFT: no invented state; no narration substituted for execution")
    print(render_chat_identity())


def _print_c2_response(response_text, runtime):
    """Render every C2 response under the canonical read-only identity nameplate."""
    from sage.agent_presence import render_chat_identity
    print(render_chat_identity())
    print(response_text)


def _build_chatgpt_client(ChatGPTClient, runtime, c2_provider):
    """Construct the client while preserving compatibility with older test seams."""
    try:
        return ChatGPTClient(runtime, c2_provider=c2_provider)
    except TypeError as exc:
        if "c2_provider" not in str(exc):
            raise
        return ChatGPTClient(runtime)


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="SAGE Autonomous Continuity Runtime CLI")
    subparsers = parser.add_subparsers(dest="command", help="SAGE commands")
    obj_parser = subparsers.add_parser("objective", help="Manage SAGE current objective"); obj_parser.add_argument("--objective", type=str)
    task_parser = subparsers.add_parser("task", help="Manage SAGE current task"); task_parser.add_argument("--task", type=str)
    subparsers.add_parser("status"); handoff_parser = subparsers.add_parser("handoff"); handoff_parser.add_argument("--file", type=str)
    restore_parser = subparsers.add_parser("restore"); restore_parser.add_argument("--file", type=str, required=True)
    snapshot_parser = subparsers.add_parser("snapshot"); snapshot_parser.add_argument("--action", choices=["create", "list", "restore"], required=True); snapshot_parser.add_argument("--file", type=str)
    ingest_parser = subparsers.add_parser("ingest"); ingest_parser.add_argument("--file", type=str, required=True)
    subparsers.add_parser("reason"); subparsers.add_parser("verify"); subparsers.add_parser("health"); subparsers.add_parser("diagnostics"); subparsers.add_parser("capabilities"); subparsers.add_parser("metrics")
    chat_parser = subparsers.add_parser("chat"); chat_mode = chat_parser.add_mutually_exclusive_group(required=True); chat_mode.add_argument("--prompt", type=str); chat_mode.add_argument("--interactive", action="store_true")
    audit_parser = subparsers.add_parser("audit"); audit_parser.add_argument("--action", choices=["summary", "diagnostics", "scan"], required=True); audit_parser.add_argument("--mission-id", type=str); audit_parser.add_argument("--archive-path", type=str, default="sage_data/archive")
    c2_parser = subparsers.add_parser("c2"); c2_parser.add_argument("--action", choices=["context", "cycle"], default="context"); c2_parser.add_argument("--action-id", type=str, default="c2_cycle_init"); c2_parser.add_argument("--description", type=str, default="C2 Governed Execution Cycle")
    business_parser = subparsers.add_parser("business", help="Expose the governed first-customer SAGE business surface")
    business_parser.add_argument("--action", choices=["preflight", "measure"], default="preflight")
    business_parser.add_argument("--workflow-id", type=str, default="")
    business_parser.add_argument("--completed", action="store_true")
    business_parser.add_argument("--human-interventions", type=int, default=0)
    business_parser.add_argument("--execution-seconds", type=float)
    business_parser.add_argument("--cost-usd", type=float)
    business_parser.add_argument("--value-usd", type=float)
    business_parser.add_argument("--failures", type=int, default=0)
    business_parser.add_argument("--recoveries", type=int, default=0)
    business_parser.add_argument("--reusable-capability", type=str)
    business_parser.add_argument("--evidence-ref", action="append", default=[])
    args = parser.parse_args(); runtime = SageRuntime()
    try:
        if args.command == "objective":
            if args.objective: print(f"Success: Objective set to '{args.objective}'\nSession ID: {runtime.set_objective(args.objective)}")
            else: print(f"Current Objective: {runtime.current_state.current_objective or 'None'}")
        elif args.command == "task":
            if args.task: print(f"Success: Task set to '{args.task}'\nSession ID: {runtime.set_task(args.task)}")
            else: print(f"Current Task: {runtime.current_state.active_task or 'None'}")
        elif args.command == "status": print(json.dumps(runtime.get_status(), indent=2))
        elif args.command == "handoff": print(f"Success: Handoff generated successfully at: '{runtime.generate_handoff(args.file)}'")
        elif args.command == "restore":
            if not runtime.restore_session(args.file): raise RuntimeError("Failed to restore session")
            print(f"Success: SAGE session state restored successfully from '{args.file}'")
        elif args.command == "snapshot":
            if args.action == "create": print(f"Success: Workspace snapshot created successfully. ID: {runtime.checkpoint()}")
            elif args.action == "list": print(json.dumps([{"snapshot_id": p.stem, "file_path": str(p), "size_bytes": p.stat().st_size} for p in runtime.workspace_path.glob("checkpoint_*.json")], indent=2))
            else:
                if not args.file or not runtime.restore_session(args.file): raise RuntimeError("Failed to restore snapshot")
        elif args.command == "ingest":
            from sage.models import ExternalSessionPayload
            with open(args.file) as f: print(json.dumps(runtime.ingest_session_payload(ExternalSessionPayload(**json.load(f))), indent=2))
        elif args.command == "reason": print(json.dumps(runtime.reason_over_continuity(), indent=2))
        elif args.command == "verify":
            result = runtime.verify_integrity(); print(json.dumps(result, indent=2)); sys.exit(0 if result.get("is_valid", False) else 1)
        elif args.command == "health":
            from sage.runtime import check_health; print(json.dumps(check_health(runtime), indent=2))
        elif args.command == "diagnostics":
            from sage.runtime import generate_diagnostic_report; print(json.dumps(generate_diagnostic_report(runtime), indent=2))
        elif args.command == "capabilities":
            from sage.runtime import generate_capability_report; print(json.dumps(generate_capability_report(runtime), indent=2))
        elif args.command == "chat":
            from sage.integration import AIQueryRequest, ChatGPTClient
            from sage.agent_presence import get_team_context
            client = _build_chatgpt_client(ChatGPTClient, runtime, get_team_context)
            _print_c2_bootstrap(runtime)
            if args.prompt:
                response = client.execute_query(AIQueryRequest(prompt=args.prompt)); _print_c2_response(response.response_text, runtime)
            else:
                session_id = None
                while True:
                    prompt = input("sage> ").strip()
                    if prompt.lower() in {"exit", "quit"}: break
                    if not prompt: continue
                    response = client.execute_query(AIQueryRequest(prompt=prompt, session_id=session_id)); session_id = response.session_id
                    _print_c2_response(response.response_text, runtime)
        elif args.command == "metrics":
            from sage.runtime import get_metrics_collector; print(json.dumps(get_metrics_collector().get_metrics(), indent=2))
        elif args.command == "audit":
            import importlib; dashboard = importlib.import_module("sage.experimental.act.act_prod_dashboard").SAGEActProdDashboard(archive_path=args.archive_path)
            if args.action == "summary": result = dashboard.retrieve_operator_summary()
            elif args.action == "diagnostics":
                result = dashboard.retrieve_mission_diagnostics(args.mission_id)
                if result is None:
                    raise RuntimeError(f"No archived trace found for mission '{args.mission_id}'")
            else: result = dashboard.handle_corrupted_archive_data()
            print(json.dumps(result, indent=2))
        elif args.command == "c2":
            from sage.agent_presence import render_team_status
            import importlib; bridge = importlib.import_module("sage.experimental.cognitive.runtime_bridge").RuntimeCognitiveBridge(runtime)
            _print_c2_bootstrap(runtime); print(render_team_status())
            if args.action == "context": print(json.dumps(bridge.get_c2_context(), indent=2, default=str))
            else: print(json.dumps(bridge.execute_cognitive_cycle(action_id=args.action_id, description=args.description).model_dump(), indent=2, default=str))
        elif args.command == "business":
            from sage.business.customer_workbench import CustomerWorkflowMeasurement, CustomerWorkbench
            from sage.c2.operator_acceptance_bootstrap import OperatorAcceptanceBootstrap
            from sage.c2.mission_continuity import CANONICAL_MAIN_GOALS
            bootstrap = OperatorAcceptanceBootstrap()
            state = bootstrap.rehydrate(
                mission_id="SAGE Operational Convergence",
                main_goals=list(CANONICAL_MAIN_GOALS),
                side_goals=[],
                active_flights=["F1", "F2", "F3", "F4", "F5"],
                required_interfaces=["chatgpt", "gemini", "jules", "observatory_hud"],
            )
            bootstrap.bind_customer_surface(state, "SAGE_FIRST_CUSTOMER", "FIRST_CUSTOMER_WORKBENCH", "[SAGE::C2::CHATGPT]")
            workbench = CustomerWorkbench("SAGE_FIRST_CUSTOMER")
            if args.action == "measure":
                if not args.workflow_id:
                    raise ValueError("--workflow-id is required for business --action measure")
                workbench.record_workflow(CustomerWorkflowMeasurement(
                    workflow_id=args.workflow_id,
                    completed=args.completed,
                    human_interventions=args.human_interventions,
                    execution_seconds=args.execution_seconds,
                    direct_cost_usd=args.cost_usd,
                    value_usd=args.value_usd,
                    reusable_capability=args.reusable_capability,
                    failure_count=args.failures,
                    recovery_count=args.recoveries,
                    evidence_refs=args.evidence_ref,
                ))
            _print_c2_bootstrap(runtime)
            print(json.dumps(workbench.snapshot(state, ["F1", "F2", "F3", "F4", "F5"]).to_dict(), indent=2))
        else: parser.print_help()
    except Exception as e:
        print(f"Error: SAGE execution failed: {e!s}"); sys.exit(1)


if __name__ == "__main__":
    main()
