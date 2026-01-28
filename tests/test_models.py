import pytest
from cortex_runtime.models.agent import AgentConfig, StepConfig

def test_valid_agent_config():
    config_data = {
        "name": "test_agent",
        "model": "cortex.llama3",
        "steps": [
            {"name": "step1", "type": "INSTRUCTION", "instruction": "do something"}
        ]
    }
    agent = AgentConfig(**config_data)
    assert agent.name == "test_agent"
    assert len(agent.steps) == 1
    assert agent.retry_policy.max_retries == 3 

def test_invalid_agent_config():
    with pytest.raises(ValueError):
        AgentConfig(name="bad", model="m", steps=[]) # Assuming steps empty is allowed but missing steps is bad? 
        # Actually pydantic will fail if types mismatch or required fields missing.
        AgentConfig(model="just model") # Missing name and steps
