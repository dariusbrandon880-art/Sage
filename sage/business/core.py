"""Business/Application Layer for SAGE - client spaces, continuous pipelines, and compliance registries."""

from typing import List, Dict, Any


class ClientWorkspaceSandbox:
    """Multi-tenant Workspace sandbox for client/project isolation."""

    def __init__(self, client_id: str, quota_bytes: int = 10 * 1024 * 1024):
        self.client_id = client_id
        self.quota_bytes = quota_bytes
        self.configs: Dict[str, Any] = {}
        self.domain_records: List[Dict[str, Any]] = []

    def set_config(self, key: str, value: Any) -> None:
        """Store a client-specific configuration value."""
        self.configs[key] = value

    def add_record(self, record_id: str, data: Dict[str, Any]) -> None:
        """Add a sandboxed data record inside the client space."""
        self.domain_records.append(
            {"record_id": record_id, "data": data, "client_id": self.client_id}
        )

    def get_records(self) -> List[Dict[str, Any]]:
        """Retrieve all sandboxed records for this client."""
        return self.domain_records


class ContinuousPipeline:
    """Business continuous pipeline representation with automated stages execution."""

    def __init__(self, name: str, stages: List[str]):
        self.name = name
        self.stages = stages
        self.stage_status: Dict[str, str] = {s: "pending" for s in stages}

    def execute_stage(self, stage_name: str, execution_fn: Any) -> bool:
        """Execute a pipeline stage and record status."""
        if stage_name not in self.stage_status:
            raise ValueError(f"Stage '{stage_name}' does not exist in pipeline '{self.name}'.")

        self.stage_status[stage_name] = "running"
        try:
            result = execution_fn()
            if result:
                self.stage_status[stage_name] = "completed"
                return True
            else:
                self.stage_status[stage_name] = "failed"
                return False
        except Exception:
            self.stage_status[stage_name] = "failed"
            return False

    def get_pipeline_status(self) -> Dict[str, str]:
        """Retrieve overall pipeline stages status."""
        return self.stage_status.copy()


class ComplianceRegistry:
    """Registry for business and corporate compliance checks."""

    def __init__(self):
        self.rules: List[Dict[str, Any]] = []

    def add_rule(self, name: str, validator_callable: Any, severity: str = "critical") -> None:
        """Add a custom compliance validation rule."""
        self.rules.append({"name": name, "validator": validator_callable, "severity": severity})

    def evaluate_compliance(self, context_data: Any) -> Dict[str, Any]:
        """Evaluate registered compliance rules against context data."""
        failed = []
        for rule in self.rules:
            try:
                is_compliant = rule["validator"](context_data)
                if not is_compliant:
                    failed.append({"rule": rule["name"], "severity": rule["severity"]})
            except Exception as e:
                failed.append({"rule": rule["name"], "severity": rule["severity"], "error": str(e)})

        return {
            "compliant": len(failed) == 0,
            "failed_rules": failed,
            "score": (len(self.rules) - len(failed)) / len(self.rules) if self.rules else 1.0,
        }
