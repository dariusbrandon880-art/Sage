"""SAGE Autonomous Continuity Runtime.

Core package for the SAGE system - providing runtime execution,
memory persistence, archive management, and ACR continuity bridging.
"""

__version__ = "0.1.0"
__author__ = "SAGE Development Team"

from sage.runtime.engine import SageRuntime
from sage.registry.core import CapabilityRegistry
from sage.intelligence.core import LLMBridge, ContextAwareRouter, PatternMatcher, ReasoningLoop
from sage.automation.core import AutomationScheduler, SelfHealingPolicy, ProactiveCheckpointer
from sage.interfaces.core import OAuthSecurityGateway, WebhookListenerRegistry, EventQueue
from sage.business.core import ClientWorkspaceSandbox, ContinuousPipeline, ComplianceRegistry

SAGERuntime = SageRuntime

__all__ = [
    "SageRuntime",
    "SAGERuntime",
    "CapabilityRegistry",
    "LLMBridge",
    "ContextAwareRouter",
    "PatternMatcher",
    "ReasoningLoop",
    "AutomationScheduler",
    "SelfHealingPolicy",
    "ProactiveCheckpointer",
    "OAuthSecurityGateway",
    "WebhookListenerRegistry",
    "EventQueue",
    "ClientWorkspaceSandbox",
    "ContinuousPipeline",
    "ComplianceRegistry"
]
