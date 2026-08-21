import argparse
import json
import sys
from pathlib import Path

from sage.runtime import SageRuntime


def main():
    parser = argparse.ArgumentParser(description="SAGE CLI")
    parser.add_argument("command", choices=["status", "chat", "capabilities", "metrics", "audit"])
    parser.add_argument("--prompt", help="Chat prompt")
    args = parser.parse_args()
    runtime = SageRuntime()

    if args.command == "status":
        print(json.dumps(runtime.get_status(), indent=2, default=str))
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

            # Keep the client constructor backward-compatible with existing test seams
            # and alternate clients; the real ChatGPT client exposes c2_provider.
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
            from sage.cli_audit import run_audit
            print(json.dumps(run_audit(), indent=2, default=str))
        except Exception as e:
            print(f"Error: Audit failed: {e!s}")
            sys.exit(1)


if __name__ == "__main__":
    main()
