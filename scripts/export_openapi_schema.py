#!/usr/bin/env python3
"""Export OpenAPI 3.0 specification from SAGE FastAPI runtime.

Generates canonical docs/openapi.json and docs/openapi.yaml for OpenAI Custom Actions
and external API integration configuration.
"""

import json
import sys
from pathlib import Path

# Prepend project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sage.experimental.observatory.server import app


def export_openapi_schema(target_root: Path = None):
    root = Path(target_root) if target_root else PROJECT_ROOT
    print("[*] Generating SAGE OpenAPI specification from live FastAPI application...")
    schema = app.openapi()

    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    json_path = docs_dir / "openapi.json"
    yaml_path = docs_dir / "openapi.yaml"

    # Export JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"[+] Exported JSON schema to: {json_path}")

    # Export YAML (manual format conversion for portability without pyyaml dependency)
    def json_to_yaml_like(data, indent=0):
        lines = []
        spacing = " " * indent
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, (dict, list)) and val:
                    lines.append(f"{spacing}{key}:")
                    lines.append(json_to_yaml_like(val, indent + 2))
                else:
                    lines.append(f"{spacing}{key}: {json.dumps(val)}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{spacing}-")
                    lines.append(json_to_yaml_like(item, indent + 2))
                else:
                    lines.append(f"{spacing}- {json.dumps(item)}")
        else:
            lines.append(f"{spacing}{json.dumps(data)}")
        return "\n".join(lines)

    yaml_content = json_to_yaml_like(schema)
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"[+] Exported YAML schema to: {yaml_path}")

    print("[+] OpenAPI export complete.")


if __name__ == "__main__":
    out_root = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    export_openapi_schema(out_root)
