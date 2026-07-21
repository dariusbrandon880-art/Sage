"""External Interfaces Layer for SAGE - secure OAuth gates, webhook listeners, and event queues."""

import queue
from typing import List, Dict, Any, Optional


class OAuthSecurityGateway:
    """Security and OAuth mock gateway for external API authentication."""

    def __init__(self):
        self.api_keys: Dict[str, str] = {}
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def register_client(self, client_id: str, client_secret: str) -> None:
        """Register client credentials."""
        self.api_keys[client_id] = client_secret

    def generate_token(self, client_id: str, client_secret: str) -> str:
        """Generate a mock OAuth bearer token."""
        if self.api_keys.get(client_id) != client_secret:
            raise PermissionError("Invalid client credentials.")

        token = f"bearer_{client_id}_access"
        self.tokens[token] = {
            "client_id": client_id,
            "active": True
        }
        return token

    def validate_token(self, token: str) -> bool:
        """Validate bearer token status."""
        token_info = self.tokens.get(token)
        return token_info is not None and token_info.get("active", False)


class WebhookListenerRegistry:
    """Registry for external webhook integration."""

    def __init__(self):
        self.listeners: Dict[str, List[str]] = {}
        self.delivered_payloads: List[Dict[str, Any]] = []

    def register_listener(self, event_type: str, url: str) -> None:
        """Register a URL to listen for specific events."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        if url not in self.listeners[event_type]:
            self.listeners[event_type].append(url)

    def trigger_event(self, event_type: str, payload: Dict[str, Any]) -> int:
        """Broadcast event payloads to all registered URL listeners."""
        urls = self.listeners.get(event_type, [])
        delivered = 0
        for url in urls:
            # Mock HTTP POST delivery
            self.delivered_payloads.append({
                "url": url,
                "event_type": event_type,
                "payload": payload
            })
            delivered += 1
        return delivered


class EventQueue:
    """Thread-safe and asynchronous-ready event buffer for external integrations."""

    def __init__(self):
        self.buffer: queue.Queue = queue.Queue()

    def push_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Push a new external event into the queue."""
        self.buffer.put({
            "event_type": event_type,
            "payload": payload
        })

    def pop_event(self) -> Optional[Dict[str, Any]]:
        """Pop the oldest event from the queue."""
        try:
            item = self.buffer.get_nowait()
            if isinstance(item, dict):
                return item
            return None
        except queue.Empty:
            return None

    def size(self) -> int:
        """Get the number of buffered events."""
        return self.buffer.qsize()
