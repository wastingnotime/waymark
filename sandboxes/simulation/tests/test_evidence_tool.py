from pathlib import Path


def test_evidence_tool_has_a_stable_entrypoint():
    tool = Path("sandboxes/simulation/tools/run_first_slice.py")
    assert tool.exists()
    assert "SimulationRunner" in tool.read_text(encoding="utf-8")
