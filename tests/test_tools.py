import pytest
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from cortex_runtime.core.engine import ExecutionEngine
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import MockProvider
from cortex_runtime.models.agent import AgentConfig

def simple_tool(input_val: str) -> str:
    return f"Processed: {input_val}"

def calculator_tool(a: int, b: int) -> int:
    return a + b

def test_tool_execution():
    # Setup
    state_manager = StateManager(session=None)
    provider = MockProvider()
    
    # 1. Define Tools
    tools = {
        "simple_tool": simple_tool,
        "calculator": calculator_tool
    }
    
    # 2. Initialize Engine with tools
    engine = ExecutionEngine(state_manager, provider, tools=tools)
    
    # 3. Validation: Direct Registry Call
    assert engine.tool_registry.execute("simple_tool", {"input_val": "test"}) == "Processed: test"
    assert engine.tool_registry.execute("calculator", {"a": 5, "b": 3}) == 8

def test_agent_tool_step():
    # Setup
    state_manager = StateManager(session=None)
    provider = MockProvider()
    
    tools = {
        "calculator": calculator_tool
    }
    engine = ExecutionEngine(state_manager, provider, tools=tools)
    
    run_id = "tool_run_1"
    config = AgentConfig(
        name="math_agent",
        model="test",
        steps=[
            # Mocking standard step config. 
            # In real system, step would have 'tool_input' dict.
            # Our engine passes 'context' as input to registry.execute.
            # So we seed context with 'a' and 'b' from previous steps or input
            {"name": "calc", "type": "TOOL_USE", "tool_name": "calculator"} 
        ]
    )
    
    state_manager.mock_add_run({
        "run_id": run_id,
        "agent_name": "math_agent",
        "status": "PENDING",
        "mock_config": config,
        "input": {"a": 10, "b": 20} # Context source
    })
    
    # Execute
    engine.execute_run(state_manager._mock_runs[run_id])
    
    # Verify
    steps = state_manager._mock_steps
    assert len(steps) == 1
    assert steps[0]['step_name'] == 'calc'
    assert steps[0]['status'] == 'SUCCESS'
    assert steps[0]['output'] == "30" # Result of 10+20

def test_env_config():
    # Test env var override
    os.environ['CR_MAX_WORKERS'] = '5'
    
    state_manager = StateManager(session=None)
    provider = MockProvider()
    engine = ExecutionEngine(state_manager, provider)
    
    assert engine.executor._max_workers == 5
    
    del os.environ['CR_MAX_WORKERS']
