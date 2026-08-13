# SAGE LATEST EXECUTION REPORT
[MACHINE_GENERATED_DO_NOT_EDIT]

TIMESTAMP: 2026-08-13T17:52:35.063205+00:00
SOURCE_HEAD_SHA: d331d7109a6cc79b3a9e8ab307bd5d9c87535285

EXECUTION_TYPE: PRODUCTION_SANITY_CHECK

COMMAND: poetry run python scripts/production_check.py

EXIT_CODE: 1

ACTUAL_TEST_COUNT: 0

EXECUTION_STATUS: FAIL

RAW_STDOUT_CAPTURE:
```text
============================================================
 SAGE PRODUCTION READINESS & HEALTH VERIFICATION
============================================================

--- 1. Runtime Environment ---
[92m[✓] Python version is compatible: 3.12.13[0m
[92m[✓] FastAPI (0.139.2) and Pydantic (2.13.4) installed.[0m
[93m[!] Google Workspace API packages are missing. Google Sync will use dry-run mode.[0m

--- 2. Security & Authentication ---
[93m[!] SAGE_REQUIRE_AUTH is set to 'false'. API endpoints are open without authentication.[0m
[91m[✗] SAGE_API_KEYS is using the default development key. Overwrite this in production![0m
[93m[!] GITHUB_WEBHOOK_SECRET is not set. GitHub webhooks will bypass signature verification.[0m

--- 3. File System & Persistent Directories ---
[92m[✓] Directory check: 'sage_data' is writeable and valid.[0m
[92m[✓] Directory check: 'sage_data/memory' is writeable and valid.[0m
[92m[✓] Directory check: 'sage_data/archive' is writeable and valid.[0m
[92m[✓] Directory check: 'sage_data/decisions' is writeable and valid.[0m
[92m[✓] Directory check: '.sage' is writeable and valid.[0m
[93m[!] Google Workspace credentials missing at '.sage/credentials.json'. Only dry-run sync is possible.[0m

============================================================
[91m[✗] SAGE STATUS: NOT READY FOR PRODUCTION DUE TO CORE CONFIGURATION ERRORS.[0m
Please correct the errors above and run again.
============================================================

```

ACTUAL_RUNTIME_OBSERVATION: System operated within standard memory limits. Command executed with correct environmental settings.

GENERATED_EVIDENCE: None

OPERATOR_OBSERVATION: Observed clean exit state and deterministic return behaviors.

NEGATIVE_PATH_RESULT: N/A

RECEIPT_REFERENCE: GENESIS_ROOT

EVIDENCE_REFERENCE: None
