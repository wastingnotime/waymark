from pathlib import Path


def test_evidence_tool_has_a_stable_entrypoint():
    tool = Path("sandboxes/simulation/tools/run_first_slice.py")
    assert tool.exists()
    source = tool.read_text(encoding="utf-8")
    assert "SimulationRunner" in source
    assert "failed_invariants" in source
    assert "return 1" in source


def test_runtime_adapter_covers_payment_provider_intentions():
    adapter = Path("sandboxes/simulation/src/app/simulation/mrl_runtime_scenario.py")
    source = adapter.read_text(encoding="utf-8")
    assert "_GRAPH_TARGET_BY_PROVIDER_ACTION" in source
    assert 'source="payment_provider"' in source


def test_runtime_adapter_covers_operator_intentions():
    adapter = Path("sandboxes/simulation/src/app/simulation/mrl_runtime_scenario.py")
    source = adapter.read_text(encoding="utf-8")
    assert "_GRAPH_TARGET_BY_OPERATOR_ACTION" in source
    assert 'source="operations"' in source


def test_runtime_adapter_covers_expiry_intentions():
    adapter = Path("sandboxes/simulation/src/app/simulation/mrl_runtime_scenario.py")
    source = adapter.read_text(encoding="utf-8")
    assert "_GRAPH_TARGET_BY_EXPIRY_ACTION" in source
    assert 'source="access_control"' in source


def test_graph_validator_has_a_stable_entrypoint():
    tool = Path("sandboxes/simulation/tools/validate_graph.py")
    assert tool.exists()
    source = tool.read_text(encoding="utf-8")
    assert "observatory_nodes" in source
    assert "observatory_edges" in source
    assert "declared graph" in source


def test_graph_validator_checks_intention_sources():
    tool = Path("sandboxes/simulation/tools/validate_graph.py")
    source = tool.read_text(encoding="utf-8")
    assert "intention_sources" in source
    assert "missing_sources" in source


def test_runtime_adapter_declares_an_explicit_event_source():
    adapter = Path("sandboxes/simulation/src/app/simulation/mrl_runtime_scenario.py")
    source = adapter.read_text(encoding="utf-8")
    assert '"event_stream"' in source
    assert '"domain_events"' in source


def test_runtime_adapter_registers_all_graph_actors():
    adapter = Path("sandboxes/simulation/src/app/simulation/mrl_runtime_scenario.py")
    source = adapter.read_text(encoding="utf-8")
    assert 'Actor("payment_provider")' in source
    assert 'Actor("support_operator")' in source
    assert 'Actor("expiry_scheduler")' in source


def test_graph_validator_checks_observation_targets():
    tool = Path("sandboxes/simulation/tools/validate_graph.py")
    source = tool.read_text(encoding="utf-8")
    assert "_GRAPH_TARGET_BY_OBSERVATION" in source
    assert "observation_targets" in source


def test_graph_validator_checks_node_metadata():
    tool = Path("sandboxes/simulation/tools/validate_graph.py")
    source = tool.read_text(encoding="utf-8")
    assert "required_node_fields" in source
    assert "invalid_node_metadata" in source


def test_graph_validator_checks_structural_beams():
    tool = Path("sandboxes/simulation/tools/validate_graph.py")
    source = tool.read_text(encoding="utf-8")
    assert "invalid_structural_beams" in source
    assert 'edge.kind != "route"' in source


def test_evidence_tool_requires_actor_intentions():
    tool = Path("sandboxes/simulation/tools/run_first_slice.py")
    source = tool.read_text(encoding="utf-8")
    assert "actor_intentions" in source
    assert "missing actor intentions" in source


def test_graph_validator_checks_runtime_actor_mapping():
    tool = Path("sandboxes/simulation/tools/validate_graph.py")
    source = tool.read_text(encoding="utf-8")
    assert "actor_graph_nodes" in source
    assert "missing_actor_nodes" in source
