"""Composite ASGI entrypoint exposing the canonical SAGE runtime plus Gemini MCP.

This keeps one runtime/service boundary: Render still serves the canonical SAGE
FastAPI application, while /mcp becomes the governed Google/Gemini interface.
"""

from sage.api import app as app
from sage.google_gemini_mcp import router as google_gemini_router

# Reuse the existing runtime, middleware, health endpoint, and authentication
# boundary. The MCP router adds no second runtime or persistence authority.
app.include_router(google_gemini_router)
