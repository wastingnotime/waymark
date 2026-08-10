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
