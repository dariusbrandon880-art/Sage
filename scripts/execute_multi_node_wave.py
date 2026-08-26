#!/usr/bin/env python3
"""Execute a canonical 3-node 5-flight + 2-reserve governed wave."""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from sage.c2.multi_node_wave import C2MultiNodeWaveEngine, NodeRole


def _flights(prefix: str, namespace_prefix: str):
    active = [
        {"flight_id": f"{prefix}_F{i}", "frontier_name": f"{prefix} Frontier {i}", "target_namespaces": [f"{namespace_prefix}/flight_{i}/"], "description": "bounded governed flight", "is_reserve": False}
        for i in range(1, 6)
    ]
    reserves = [
        {"flight_id": f"{prefix}_R{i}", "frontier_name": f"{prefix} Reserve {i}", "target_namespaces": [f"{namespace_prefix}/reserve_{i}/"], "description": "bounded reserve", "is_reserve": True}
        for i in range(1, 3)
    ]
    return active + reserves


def main() -> int:
    engine = C2MultiNodeWaveEngine(repo_root=repo_root)
    nodes = {
        "NODE_A": {"role": NodeRole.PRIMARY_REPAIR.value, "flights": _flights("A", "sage/experimental/airspace")},
        "NODE_B": {"role": NodeRole.INDEPENDENT_VERIFICATION.value, "flights": _flights("B", "tests/c2")},
        "NODE_C": {"role": NodeRole.ADVERSARIAL_RESEARCH.value, "flights": _flights("C", "adversarial")},
    }
    receipt = engine.execute_multi_node_wave("WAVE_MULTI_NODE_CURRENT_HEAD", nodes)
    evidence = repo_root / "evidence_capture" / "multi_node_wave_evidence.json"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(receipt.to_dict(), indent=2) + "\n", encoding="utf-8")
    print(f"{receipt.reconvergence_verdict}: {receipt.commit_sha} receipt={receipt.receipt_hash}")
    return 0 if receipt.reconvergence_verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
