import pytest
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from cortex_runtime.core.engine import ExecutionEngine
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import MockProvider
from cortex_runtime.models.agent import AgentConfig

def test_concurrent_execution():
    """
    Simulate a batch of runs and ensure they are processed.
    Note: Threading tests are tricky in unit tests. We verify the machinery works.
    """
    state_manager = StateManager(session=None)
    provider = MockProvider()
    engine = ExecutionEngine(state_manager, provider, max_workers=5)
    
    # Create config
    config = AgentConfig(name="test_agent", model="mock", steps=[
        {"name": "s1", "instruction": "wait"}
    ])
    
    # Inject 5 runs
    run_ids = [f"run_{i}" for i in range(5)]
    for rid in run_ids:
        state_manager.mock_add_run({
            "run_id": rid,
            "agent_name": "test_agent",
            "status": "PENDING",
            "mock_config": config,
            "input": {}
        })
        
    # Manually trigger the batch fetch and submit logic (avoiding infinite while True)
    # 1. Fetch
    pending = state_manager.fetch_pending_runs(limit=10)
    assert len(pending) == 5
    
    # 2. Submit
    futures = []
    for run in pending:
        # Submit to executor directly
        f = engine.executor.submit(engine.execute_run, run)
        futures.append(f)
        
    # 3. Wait for all to complete
    for f in futures:
        f.result() # Blocks until done
        
    # 4. Verify all completed
    for rid in run_ids:
        assert state_manager._mock_runs[rid]['status'] == 'COMPLETED'
