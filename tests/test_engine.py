import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from cortex_runtime.core.engine import ExecutionEngine
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import LLMProvider, LLMResult, MockProvider
from cortex_runtime.models.agent import AgentConfig

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
    assert "Explicit Mock Output" in steps[0]['output'] # Matches the new MockProvider
    assert steps[0]['tokens_used'] == 0
    assert steps[0]['model'] == 'test_model'

def test_engine_resume_run():
    # Setup
    state_manager = StateManager(session=None)
    provider = MockProvider()
    engine = ExecutionEngine(state_manager, provider)
    
    run_id = "failed_run"
    state_manager.mock_add_run({
        "run_id": run_id,
        "agent_name": "test_agent",
        "status": "FAILED",
        "input": {}
    })
    
    # Verify initial state
    assert state_manager._mock_runs[run_id]['status'] == 'FAILED'
    
    # Action
    engine.resume_run(run_id)
    
    # Assert
    assert state_manager._mock_runs[run_id]['status'] == 'PENDING'

def test_resume_skips_steps():
    # Setup
    state_manager = StateManager(session=None)
    provider = MockProvider()
    engine = ExecutionEngine(state_manager, provider)
    
    config = AgentConfig(
        name="test_agent",
        model="test_model",
        steps=[
            {"name": "s1", "instruction": "prompt1"},
            {"name": "s2", "instruction": "prompt2"}
        ]
    )
    
    run_id = "partial_run"
    # Run Mock: has 1 step completed
    state_manager.mock_add_run({
        "run_id": run_id,
        "agent_name": "test_agent",
        "status": "PENDING", # Resumed status
        "mock_config": config,
        "input": {},
        "completed_steps": 1 # The fetcher would theoretically return this
    })
    
    # Execute
    engine.execute_run(state_manager._mock_runs[run_id])
    
    # Assertions
    steps = state_manager._mock_steps
    assert len(steps) == 1 # only s2 should run
    assert steps[0]['step_name'] == 's2'

def test_engine_get_summary():
    # Setup
    state_manager = StateManager(session=None)
    provider = MockProvider()
    engine = ExecutionEngine(state_manager, provider)
    
    summary = engine.get_run_summary("any_id")
    assert summary['run_id'] == "any_id"
    assert summary['total_tokens'] == 0

