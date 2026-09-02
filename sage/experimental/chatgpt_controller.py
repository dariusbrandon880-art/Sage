"""ChatGPT Controller Re-export for Experimental Surface.

Re-exports ChatGPTController, ChatRenderRequest, and ChatRenderResponse from
the canonical SAGE C2 module (sage.c2.chatgpt_controller).
"""

from sage.c2.chatgpt_controller import (
    ChatGPTController,
    ChatRenderRequest,
    ChatRenderResponse,
)

__all__ = ["ChatGPTController", "ChatRenderRequest", "ChatRenderResponse"]
