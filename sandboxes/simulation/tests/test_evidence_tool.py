from pathlib import Path


def test_evidence_tool_has_a_stable_entrypoint():
    tool = Path("sandboxes/simulation/tools/run_first_slice.py")
    assert tool.exists()
    source = tool.read_text(encoding="utf-8")
    assert "SimulationRunner" in source
    assert "failed_invariants" in source
    assert "return 1" in source
