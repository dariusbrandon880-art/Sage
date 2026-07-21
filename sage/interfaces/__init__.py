"""SAGE External Interfaces Layer - OAuth, webhooks, and queues."""

from sage.interfaces.core import OAuthSecurityGateway, WebhookListenerRegistry, EventQueue

__all__ = ["OAuthSecurityGateway", "WebhookListenerRegistry", "EventQueue"]
