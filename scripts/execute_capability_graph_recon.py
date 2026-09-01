#!/usr/bin/env python3
"""Run a repo-native capability graph reconnaissance against an exact HEAD."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sage.c2.capability_graph import CapabilityGraphEngine


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact-head", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--output", default="evidence_capture/capability_graph_recon.json")
    args = parser.parse_args()

    if len(args.exact_head) != 40:
        raise SystemExit("exact HEAD must be a 40-character SHA")

    engine = CapabilityGraphEngine(args.root)
    graph = engine.discover(args.exact_head)
    missions = engine.rank_missions(graph, args.limit)
    payload = {
        "exact_git_head": graph.exact_git_head,
        "graph_digest": graph.digest,
        "node_count": len(graph.nodes),
        "surfaces": sorted({node.surface for node in graph.nodes}),
        "missions": [mission.__dict__ for mission in missions],
        "mission_surface_count": len({mission.surface for mission in missions}),
        "verdict": "PASS" if missions else "FAILED_CLOSED",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
