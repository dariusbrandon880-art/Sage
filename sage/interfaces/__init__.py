"""SAGE External Interfaces Layer - OAuth, webhooks, and queues."""

from sage.interfaces.core import OAuthSecurityGateway, WebhookListenerRegistry, EventQueue
from sage.interfaces.integrations import SAGEIntegrationManager

__all__ = [
    "OAuthSecurityGateway",
    "WebhookListenerRegistry",
    "EventQueue",
    "SAGEIntegrationManager",
]
