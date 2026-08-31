"""Speaker/provenance boundary for SAGE cross-station conversation relays."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

PROVENANCE_VERSION = "conversation-provenance-v0.1"

class Station(StrEnum):
    DIRECTOR = "[SAGE::DIRECTOR]"
    C2_CHATGPT = "[SAGE::C2::CHATGPT]"
    ENGINEER_JULES = "[SAGE::ENGINEER::JULES]"
    INTEL_GEMINI = "[SAGE::INTEL::GEMINI]"
    GOOGLE_BUILDER = "[SAGE::C2::GOOGLE]"
    JULES_BUILDER = "[SAGE::C2::JULES]"

@dataclass(frozen=True)
class ConversationEnvelope:
    """Immutable provenance for one human or station message."""
    sender: Station
    recipient: Station
    content: str
    source: str
    message_kind: str = "message"
    conversation_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("content must be a non-empty string")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string")
        if self.sender == self.recipient:
            raise ValueError("sender and recipient must be distinct stations")

    @property
    def provenance_label(self) -> str:
        return f"{self.sender.value} -> {self.recipient.value}"

    def to_dict(self) -> dict[str, str | None]:
        return {
            "provenance_version": PROVENANCE_VERSION,
            "sender": self.sender.value,
            "recipient": self.recipient.value,
            "content": self.content,
            "source": self.source,
            "message_kind": self.message_kind,
            "conversation_id": self.conversation_id,
        }

def classify_director_input(content: str, *, conversation_id: str | None = None) -> ConversationEnvelope:
    """Mark operator input explicitly as Director input to C2."""
    return ConversationEnvelope(
        sender=Station.DIRECTOR, recipient=Station.C2_CHATGPT,
        content=content, source="operator_input", message_kind="director_input",
        conversation_id=conversation_id,
    )

def classify_relayed_station_message(*, sender: Station, content: str,
    source: str = "human_relay", conversation_id: str | None = None,
    recipient: Station = Station.C2_CHATGPT) -> ConversationEnvelope:
    """Preserve a relayed station report as quoted provenance."""
    if sender == Station.DIRECTOR:
        raise ValueError("use classify_director_input for Director input")
    return ConversationEnvelope(
        sender=sender, recipient=recipient, content=content, source=source,
        message_kind="station_relay", conversation_id=conversation_id,
    )

def distinguish_input_from_relay(*, director_content: str,
    relayed_messages: Mapping[Station, str] | None = None,
    conversation_id: str | None = None) -> dict[str, object]:
    """Build a deterministic context boundary separating Director input from relays."""
    envelopes = [
        classify_relayed_station_message(sender=sender, content=content,
            conversation_id=conversation_id)
        for sender, content in (relayed_messages or {}).items()
    ]
    return {
        "provenance_version": PROVENANCE_VERSION,
        "director_input": classify_director_input(director_content,
            conversation_id=conversation_id).to_dict(),
        "relayed_station_messages": [item.to_dict() for item in envelopes],
        "canonical_truth": "repository_and_validated_archive",
        "relay_authority": "non_canonical_input_until_reconciled",
    }
