"""SAGE Capability Reporting - dynamic reporting of system capabilities and active integrations."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from sage.runtime.metrics import get_metrics_collector


def generate_capability_report(runtime: Optional[Any] = None) -> Dict[str, Any]:
    """Assess and return the dynamic availability of SAGE platform capabilities.

    Args:
        runtime: Active SAGE runtime instance to inspect.

    Returns:
        Structured capability status report.
    """
    metrics = get_metrics_collector()
    metrics.increment("capabilities_reports.total")
    metrics.record_event("capabilities_report.generated")

    # 1. Runtime Capabilities
    runtime_caps = [
        {
            "name": "state_persistence",
            "description": "Continuous, atomic serialization of active objectives and task states",
            "status": "enabled" if runtime is not None else "supported",
            "details": {}
        },
        {
            "name": "checkpointing",
            "description": "On-demand, full database and state serialization checkpoints",
            "status": "enabled" if runtime is not None else "supported",
            "details": {}
        },
        {
            "name": "handoff_generation",
            "description": "Exporting full system context and session lineage for handoff transitions",
            "status": "enabled" if runtime is not None else "supported",
            "details": {}
        },
        {
            "name": "workspace_snapshots",
            "description": "Granular snapshots stored under .sage/sage_state.json for fast reboot hydration",
            "status": "enabled" if runtime is not None else "supported",
            "details": {}
        }
    ]

    # 2. ACR Capabilities
    enable_continuity = True
    if runtime is not None and hasattr(runtime, "config"):
        enable_continuity = runtime.config.get("enable_continuity", True)

    acr_caps = [
        {
            "name": "continuity_bridge",
            "description": "A single authoritative ingestion pipeline mapping raw interactions into state",
            "status": "active" if (runtime is not None and enable_continuity) else "disabled" if not enable_continuity else "supported",
            "details": {"enable_continuity": enable_continuity}
        },
        {
            "name": "session_lineage",
            "description": "Tracing chain of custody and sessions through persistent DAG links",
            "status": "active" if runtime is not None else "supported",
            "details": {}
        },
        {
            "name": "auto_git_continuity_capture",
            "description": "Auto-capture of workspace branch/diff state and formatting as external payloads",
            "status": "active" if runtime is not None else "supported",
            "details": {}
        }
    ]

    # 3. Archive Capabilities
    archive_caps = [
        {
            "name": "historical_logging",
            "description": "Write-once timeline logging of validated and promoted platform milestones",
            "status": "active" if (runtime is not None and getattr(runtime, "archive", None) is not None) else "supported",
            "details": {}
        },
        {
            "name": "archive_promotion",
            "description": "Structured rules promoting verified memories to the canonical long-term archive",
            "status": "active" if (runtime is not None and getattr(runtime, "validation", None) is not None) else "supported",
            "details": {}
        },
        {
            "name": "filtered_search",
            "description": "Advanced querying over historical events by type, title, and timestamp boundaries",
            "status": "active" if (runtime is not None and getattr(runtime, "archive", None) is not None) else "supported",
            "details": {}
        }
    ]

    # 4. Memory Capabilities
    memory_caps = [
        {
            "name": "short_term_context",
            "description": "Ephemeral execution context tracking active tasks and current turn number",
            "status": "active" if (runtime is not None and getattr(runtime, "context", None) is not None) else "supported",
            "details": {}
        },
        {
            "name": "long_term_storage",
            "description": "Database memory objects categorized by confidence scores and tags",
            "status": "active" if (runtime is not None and getattr(runtime, "memory", None) is not None) else "supported",
            "details": {}
        },
        {
            "name": "tag_based_search",
            "description": "Fast retrieval of memory nodes by indexed tags and object types",
            "status": "active" if (runtime is not None and getattr(runtime, "memory", None) is not None) else "supported",
            "details": {}
        }
    ]

    # 5. Integration Capabilities
    # Read environment to assess live integrations
    import os
    has_chatgpt = bool(os.getenv("OPENAI_API_KEY"))
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_gh_secret = bool(os.getenv("GITHUB_WEBHOOK_SECRET"))
    has_google_creds = os.path.exists(".sage/credentials.json") or bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    integration_caps = [
        {
            "name": "chatgpt_connector",
            "description": "Dynamic context-retrieval routing through ChatGPT Custom Actions",
            "status": "active" if has_chatgpt else "unconfigured",
            "details": {"has_api_key": has_chatgpt}
        },
        {
            "name": "gemini_jules_connector",
            "description": "Native multi-turn reasoning and agent execution through Gemini/Jules APIs",
            "status": "active" if has_gemini else "unconfigured",
            "details": {"has_api_key": has_gemini}
        },
        {
            "name": "github_webhook_listener",
            "description": "Secure, HMAC-verified webhook handler for inbound push, pr, and repo events",
            "status": "active" if has_gh_secret else "supported_unsecure",
            "details": {"hmac_verification_enabled": has_gh_secret}
        },
        {
            "name": "google_workspace_sync",
            "description": "Bidirectional synchronizer exporting docs to Google Docs and trackers to Sheets",
            "status": "active" if has_google_creds else "dry_run_only",
            "details": {"credentials_found": has_google_creds}
        }
    ]

    total_capabilities = len(runtime_caps) + len(acr_caps) + len(archive_caps) + len(memory_caps) + len(integration_caps)
    active_capabilities = (
        sum(1 for c in runtime_caps if c["status"] == "active" or c["status"] == "enabled") +
        sum(1 for c in acr_caps if c["status"] == "active" or c["status"] == "enabled") +
        sum(1 for c in archive_caps if c["status"] == "active" or c["status"] == "enabled") +
        sum(1 for c in memory_caps if c["status"] == "active" or c["status"] == "enabled") +
        sum(1 for c in integration_caps if c["status"] == "active" or c["status"] == "enabled")
    )

    metrics.set_gauge("capabilities.total_count", float(total_capabilities))
    metrics.set_gauge("capabilities.active_count", float(active_capabilities))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_capabilities": total_capabilities,
        "active_capabilities": active_capabilities,
        "runtime_capabilities": runtime_caps,
        "acr_capabilities": acr_caps,
        "archive_capabilities": archive_caps,
        "memory_capabilities": memory_caps,
        "integration_capabilities": integration_caps,
    }
