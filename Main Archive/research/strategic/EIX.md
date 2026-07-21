# External Interface Gateway (EIX) Spec

The External Interface Gateway governs secure, multi-protocol communication between the SAGE runtime and third-party systems.

## 1. Concept Overview
The EIX establishes the security boundary of SAGE, offering:
- **API Token Verification**: Authorizes external REST queries using securely mapped bearer tokens compared against `SAGE_API_KEYS`.
- **OAuth 2.0 Integration**: Handles OAuth token exchanges to authenticate ChatGPT Action extensions or Google Workspace API requests.
- **Payload Sanitization**: Inspects incoming JSON objects to prevent SQL injection, path traversal, or command execution vulnerabilities.

## 2. Portability & High-Concurrency
EIX utilizes asynchronous ASGI routers (FastAPI) to handle high-concurrency event ingestion without blocking the core SAGE-ACR execution loop.
