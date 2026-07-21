# Event Integration Layer (EIL) Spec

The Event Integration Layer models all external operations—such as code merges, document modifications, and shell executions—as streamable events within SAGE.

## 1. Concept Overview
Instead of periodically polling repositories or Google Drive folders, EIL processes incoming streams of events in real-time:
- **`GitHubEvent` Ingestion**: Webhook events capture commit hashes, branch refs, and pull-request states.
- **`GoogleWorkspaceArtifact` Ingestion**: Capture when Google docs are created, updated, or modified.
- **Unified Event Queue**: Events are indexed chronologically and mapped directly into SAGE's short-term memory layer for validation.

## 2. Event Routing
Once ingested, events are matched against active objectives. For example, a successful pull request event will trigger SAGE to automatically transition the corresponding task from active to validated.
