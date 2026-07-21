# Subject Matter Expert (SME) Layer Spec

The Subject Matter Expert (SME) Layer is the cognitive router of SAGE. It bridges high-level user intentions to specific functional systems.

## 1. Concept Overview
The SME Layer is designed to:
- Parse natural language queries and extract key architectural intentions.
- Classify tasks according to domain-specific areas (e.g. database schema migrations, CI/CD pipeline automation, API design).
- Load corresponding memory schemas and quality assurance rule-sets.

## 2. Dynamic Router Model
When a user sets an objective, the SME router maps the task to active capability endpoints:
```
                     User Objective
                           │
                           ▼
                 Intent Classification
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
       [Database]       [API]         [Pipeline]
```
Each domain has specialized prompt templates and contextual memory priorities.
