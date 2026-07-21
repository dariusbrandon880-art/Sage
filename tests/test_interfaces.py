"""Tests for SAGE External Interfaces Layer."""

import pytest
from sage.interfaces.core import OAuthSecurityGateway, WebhookListenerRegistry, EventQueue


def test_oauth_security_gateway():
    """Test OAuth key registry and security bearer token flow."""
    gw = OAuthSecurityGateway()
    gw.register_client("sage_cli", "super_secret_123")

    # 1. Invalid credentials
    with pytest.raises(PermissionError):
        gw.generate_token("sage_cli", "wrong_secret")

    # 2. Valid credentials
    token = gw.generate_token("sage_cli", "super_secret_123")
    assert token.startswith("bearer_")

    # 3. Validate
    assert gw.validate_token(token) is True
    assert gw.validate_token("invalid_bearer_token") is False


def test_webhook_listener_registry():
    """Test registering webhooks and triggering broadcasts."""
    registry = WebhookListenerRegistry()
    registry.register_listener("checkpoint_created", "https://api.external.com/v1/checkpoint")
    registry.register_listener("checkpoint_created", "https://api.backup.com/hooks")
    registry.register_listener("session_ended", "https://api.external.com/v1/session_end")

    # Trigger first event
    delivered_count = registry.trigger_event(
        "checkpoint_created", {"id": "checkpoint_abc", "state": "saved"}
    )
    assert delivered_count == 2
    assert len(registry.delivered_payloads) == 2
    assert registry.delivered_payloads[0]["url"] == "https://api.external.com/v1/checkpoint"
    assert registry.delivered_payloads[1]["url"] == "https://api.backup.com/hooks"

    # Trigger second event
    delivered_count2 = registry.trigger_event("session_ended", {"session_id": "session_123"})
    assert delivered_count2 == 1


def test_event_queue():
    """Test thread-safe integration event queue buffering."""
    eq = EventQueue()
    assert eq.size() == 0

    eq.push_event("webhook_received", {"source": "github", "ref": "main"})
    eq.push_event("api_request", {"user": "admin"})
    assert eq.size() == 2

    first_event = eq.pop_event()
    assert first_event["event_type"] == "webhook_received"
    assert first_event["payload"]["source"] == "github"

    second_event = eq.pop_event()
    assert second_event["event_type"] == "api_request"

    # Pop empty queue
    assert eq.pop_event() is None
    assert eq.size() == 0
