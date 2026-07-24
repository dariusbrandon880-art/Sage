"""Runtime engine and intelligence layers for SAGE autonomous operations.

Establishes the invariant sage.runtime:app export boundary.
"""

from sage.runtime.capability_report import discover_capabilities, generate_capability_report
from sage.runtime.diagnostics import (
    InitializationManager,
    generate_diagnostic_report,
    generate_system_status_report,
)
from sage.runtime.engine import SageRuntime
from sage.runtime.health import check_health, get_sage_identity
from sage.runtime.metrics import get_metrics_collector

SAGERuntime = SageRuntime


# --- SAGE Runtime Integrity Layer (SRIL) Phase 1 Invariant app export boundary ---


class SYNTACTIC_PATH_MISALIGNMENT(ImportError):
    """Raised when there is a directory structure or path routing failure."""


class SYNTACTIC_INTERFACE_DRIFT(AttributeError):
    """Raised when the expected interface or attribute differs from current state."""


class SEMANTIC_INITIALIZATION_EXCEPTION(RuntimeError):
    """Raised when the application fails semantically on initialization."""


try:
    from sage.api import app as fastapi_app

    app = fastapi_app
except ImportError as e:
    raise SYNTACTIC_PATH_MISALIGNMENT(
        "SAGE Runtime SYNTACTIC_PATH_MISALIGNMENT: Could not find or route sage.api module."
    ) from e
except AttributeError as e:
    raise SYNTACTIC_INTERFACE_DRIFT(
        "SAGE Runtime SYNTACTIC_INTERFACE_DRIFT: Attribute mismatch on App boundaries."
    ) from e
except Exception as e:
    raise SEMANTIC_INITIALIZATION_EXCEPTION(
        "SAGE Runtime SEMANTIC_INITIALIZATION_EXCEPTION: Semantic crash during app startup."
    ) from e


__all__ = [
    "SEMANTIC_INITIALIZATION_EXCEPTION",
    "SYNTACTIC_INTERFACE_DRIFT",
    "SYNTACTIC_PATH_MISALIGNMENT",
    "InitializationManager",
    "SAGERuntime",
    "SageRuntime",
    "app",
    "check_health",
    "discover_capabilities",
    "generate_capability_report",
    "generate_diagnostic_report",
    "generate_system_status_report",
    "get_metrics_collector",
    "get_sage_identity",
]
