import pytest
from unittest.mock import MagicMock
from cortex_runtime.core.engine import ExecutionEngine
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import LLMProvider, LLMResult
from cortex_runtime.models.agent import AgentConfig

class MockProvider(LLMProvider):
    def generate(self, prompt, model, config):
        return LLMResult(text="mock response", tokens_used=10, latency_ms=10)

def test_engine_execution_flow():
    # Setup
    state_manager = StateManager(session=None) # Mock mode
    provider = MockProvider()
    engine = ExecutionEngine(state_manager, provider)
    
    # Inject Run
    config = AgentConfig(
        name="test_agent",
        model="test_model",
        steps=[
            {"name": "s1", "instruction": "prompt1"}
        ]
    )
    
    run_id = "test_run_1"
    state_manager.mock_add_run({
        "run_id": run_id,
        "agent_name": "test_agent",
        "status": "PENDING",
        "mock_config": config,
        "input": {}
    })
    
    # Execute one cycle checks
    pending = state_manager.fetch_pending_runs()
    assert len(pending) == 1
    
    # Run the specific run logic manually to avoid infinite loop
    engine.execute_run(pending[0])
    
    # Assertions
    run_status = state_manager._mock_runs[run_id]['status']
    assert run_status == 'COMPLETED'
    
    steps = state_manager._mock_steps
    assert len(steps) == 1
    assert steps[0]['step_name'] == 's1'
    assert steps[0]['output'] == 'mock response'
