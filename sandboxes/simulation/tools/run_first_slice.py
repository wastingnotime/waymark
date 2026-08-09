#!/usr/bin/env python3
"""Run the Waymark scenario and write its observation log as JSONL."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from app.simulation.mrl_runtime_scenario import create_simulation
from mrl_simulation_runtime.runner import SimulationRunner


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write JSONL evidence to this file")
    args = parser.parse_args()

    result = SimulationRunner().run(create_simulation())
    jsonl = result.observations.to_jsonl()
    failed_invariants = [
        observation.name
        for observation in result.observations.observations
        if observation.type == "invariant_result" and observation.payload.get("passed") is False
    ]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(jsonl, encoding="utf-8")
        print(f"wrote {len(result.observations.observations)} observations to {args.output}")
    else:
        print(jsonl, end="")
    if failed_invariants:
        print(f"failed invariants: {', '.join(failed_invariants)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
