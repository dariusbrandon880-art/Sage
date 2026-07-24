# SAGE COMMAND CENTER - Operational Control Manual

This document provides complete instructions for starting, managing, querying, and verifying SAGE.

---

## 1. System Requirements & Environment Startup

### Installation
Ensure that python dependencies are installed correctly:
```bash
pip install -e ".[dev]"
```

### Starting the REST API Server
The SAGE REST API is powered by FastAPI and Uvicorn. Start the server on port 8000:
```bash
uvicorn sage.api:app --host 0.0.0.0 --port 8000
```

To secure the service lifecycle hooks `/service/startup` and `/service/shutdown`, set the environment variable:
```bash
export SAGE_API_KEYS="secure-admin-token-xyz"
```

---

## 2. Command Line Interface (CLI) Manual
SAGE includes a complete CLI engine (`sage/cli.py`) for local scripting and interaction.

### General Usage
```bash
python -m sage.cli --help
```

### Commands
- **Set the Active Objective**:
  ```bash
  python -m sage.cli objective --objective "Implement SAGE live connectors"
  ```
- **Set/Update Current Task**:
  ```bash
  python -m sage.cli task --task "Write canonical documentation layout"
  ```
- **View Full Status (JSON Output)**:
  ```bash
  python -m sage.cli status
  ```
- **Generate Continuity Handoff**:
  ```bash
  python -m sage.cli handoff --file path/to/handoff.json
  ```
- **Restore State from Handoff**:
  ```bash
  python -m sage.cli restore --file path/to/handoff.json
  ```
- **Create Workspace Snapshot Checkpoint**:
  ```bash
  python -m sage.cli snapshot --action create
  ```

---

## 3. REST API Endpoint Reference
The server provides a standard set of endpoints under `/docs` (interactive Swagger UI).

### Continuity Loops
- `POST /objective` / `GET /objective` - Retrieve/Set active system objectives.
- `POST /task` / `GET /task` - Retrieve/Set current tasks.
- `POST /blocker` / `DELETE /blocker` - Manage blocking issues in continuous pipelines.

### Knowledge Operations
- `POST /memory` - Ingest a draft MemoryObject.
- `POST /validate` - Evaluate a memory object against rules.
- `POST /promote/validated` - Mark memory as validated.
- `POST /promote/archive` - Promote validated memory into the Master Archive.

### External Tool Ingestion
- `POST /tools/github/event` - Index commit or PR event.
- `POST /tools/workspace/artifact` - Index a Google Workspace documentation url.
- `GET /tools/index/relationships` - Cross-reference commits and documents.

### SAGE-SKAL Promoted Lineage Entry: skal_deployment_event_d9742fac
- **Timestamp**: 2026-07-24T03:18:21.386460+00:00
- **Payload Type**: `deployment_event`
- **Title/Subject**: Deployment to production-onrender (synchronized)
- **Lineage Details**: Deployment event parsed. Operational state updated by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_deployment_event_a677c4be
- **Timestamp**: 2026-07-24T03:19:50.223822+00:00
- **Payload Type**: `deployment_event`
- **Title/Subject**: Deployment to production-onrender (synchronized)
- **Lineage Details**: Deployment event parsed. Operational state updated by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_deployment_event_bc770957
- **Timestamp**: 2026-07-24T03:27:08.462969+00:00
- **Payload Type**: `deployment_event`
- **Title/Subject**: Deployment to production-onrender (synchronized)
- **Lineage Details**: Deployment event parsed. Operational state updated by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_deployment_event_014be154
- **Timestamp**: 2026-07-24T03:30:52.614990+00:00
- **Payload Type**: `deployment_event`
- **Title/Subject**: Deployment to production-onrender (synchronized)
- **Lineage Details**: Deployment event parsed. Operational state updated by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_deployment_event_46262c64
- **Timestamp**: 2026-07-24T05:23:46.418527+00:00
- **Payload Type**: `deployment_event`
- **Title/Subject**: Deployment to production-onrender (synchronized)
- **Lineage Details**: Deployment event parsed. Operational state updated by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_deployment_event_89fc6691
- **Timestamp**: 2026-07-24T05:28:33.128738+00:00
- **Payload Type**: `deployment_event`
- **Title/Subject**: Deployment to production-onrender (synchronized)
- **Lineage Details**: Deployment event parsed. Operational state updated by Jules.

### SAGE-SKAL Promoted Lineage Entry: skal_deployment_event_74482f79
- **Timestamp**: 2026-07-24T05:30:26.391987+00:00
- **Payload Type**: `deployment_event`
- **Title/Subject**: Deployment to production-onrender (synchronized)
- **Lineage Details**: Deployment event parsed. Operational state updated by Jules.
