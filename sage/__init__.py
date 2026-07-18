"""SAGE Autonomous Continuity Runtime.

Core package for the SAGE system - providing runtime execution,
memory persistence, archive management, and ACR continuity bridging.
"""

__version__ = "0.1.0"
__author__ = "SAGE Development Team"

from sage.runtime.engine import SageRuntime

__all__ = ["SageRuntime"]
