from typing import Dict, Any, Optional, Protocol, runtime_checkable
from pydantic import BaseModel
import time

class LLMResult(BaseModel):
    text: str
    tokens_used: int
    latency_ms: float
    raw_response: Optional[Dict[str, Any]] = None

@runtime_checkable
class LLMProvider(Protocol):
    """
    Protocol defining the interface for any LLM backend.
    This allows us to swap Cortex for OpenAI, Azure, or Mock providers easily.
    """
    def generate(self, prompt: str, model: str, config: Dict[str, Any]) -> LLMResult:
        ...

class CortexProvider:
    """
    Snowflake Cortex implementation of the LLMProvider protocol.
    """
    def __init__(self, session=None):
        self.session = session

    def generate(self, prompt: str, model: str, config: Dict[str, Any]) -> LLMResult:
        start_time = time.time()
        
        # In a real environment, we would use self.session.sql(...)
        # For this skeletal implementation, we will mock the call if session is None
        
        if self.session:
            # Placeholder for actual Snowpark Cortex call
            # result = self.session.sql(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{prompt}')").collect()
            # return parse_result(result)
            pass
        
        # Fallback / Mock behavior if session is missing (for local testing)
        latency = (time.time() - start_time) * 1000
        return LLMResult(
            text=f"Mock response from {model} for prompt: {prompt[:50]}...",
            tokens_used=len(prompt.split()) + 10,
            latency_ms=latency,
            raw_response={"mock": True}
        )

class MockProvider:
    """
    Explicit Mock provider for testing.
    """
    def generate(self, prompt: str, model: str, config: Dict[str, Any]) -> LLMResult:
        return LLMResult(
            text="Explicit Mock Output",
            tokens_used=0,
            latency_ms=0,
            raw_response={}
        )

# Factory to get provider
def get_llm_provider(provider_type: str = "cortex", session=None) -> LLMProvider:
    if provider_type.lower() == "cortex":
        return CortexProvider(session)
    elif provider_type.lower() == "mock":
        return MockProvider()
    raise ValueError(f"Unknown provider type: {provider_type}")
