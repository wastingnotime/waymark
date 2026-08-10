"""Validate the simulation's declared observatory graph contract."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "sandboxes" / "simulation" / "src"))

from app.simulation.mrl_runtime_scenario import (  # noqa: E402
    _GRAPH_TARGET_BY_OBSERVATION,
    _GRAPH_TARGET_BY_EXPIRY_ACTION,
    _GRAPH_TARGET_BY_OPERATOR_ACTION,
    _GRAPH_TARGET_BY_PROVIDER_ACTION,
    _GRAPH_TARGET_BY_SUBSCRIBER_ACTION,
    create_simulation,
)


def main() -> int:
    scenario = create_simulation()
    node_ids = {node.id for node in scenario.observatory_nodes}
    if len(node_ids) != len(scenario.observatory_nodes):
        raise SystemExit("declared graph contains duplicate node ids")

    required_node_fields = ("realm", "domain", "layer", "status")
    invalid_node_metadata = [
        node.id
        for node in scenario.observatory_nodes
        if node.realm != "waymark" or any(not getattr(node, field) for field in required_node_fields)
    ]
    if invalid_node_metadata:
        raise SystemExit(f"declared graph has invalid node metadata: {invalid_node_metadata}")

    for edge in scenario.observatory_edges:
        if edge.from_node not in node_ids or edge.to_node not in node_ids:
            raise SystemExit(f"declared graph has an edge endpoint outside its nodes: {edge}")

    invalid_structural_beams = [
        edge
        for edge in scenario.observatory_edges
        if edge.kind != "route" or not edge.label.strip()
    ]
    if invalid_structural_beams:
        raise SystemExit(f"declared graph has invalid structural beams: {invalid_structural_beams}")

    mapped_targets = set().union(
        _GRAPH_TARGET_BY_OBSERVATION.values(),
        _GRAPH_TARGET_BY_SUBSCRIBER_ACTION.values(),
        _GRAPH_TARGET_BY_PROVIDER_ACTION.values(),
        _GRAPH_TARGET_BY_OPERATOR_ACTION.values(),
        _GRAPH_TARGET_BY_EXPIRY_ACTION.values(),
    )
    missing_targets = mapped_targets - node_ids
    if missing_targets:
        raise SystemExit(f"declared graph is missing mapped targets: {sorted(missing_targets)}")

    observation_targets = set(_GRAPH_TARGET_BY_OBSERVATION.values())
    if not observation_targets <= node_ids:
        missing_observation_targets = observation_targets - node_ids
        raise SystemExit(
            "declared graph is missing observation targets: "
            f"{sorted(missing_observation_targets)}"
        )

    intention_sources = {"subscriber", "payment_provider", "operations", "access_control"}
    missing_sources = intention_sources - node_ids
    if missing_sources:
        raise SystemExit(f"declared graph is missing intention sources: {sorted(missing_sources)}")

    print(
        f"declared graph valid: {len(scenario.observatory_nodes)} nodes, "
        f"{len(scenario.observatory_edges)} edges"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
