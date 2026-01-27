from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class RetryPolicy(BaseModel):
    max_retries: int = 3
    retry_on_status: List[str] = Field(default_factory=lambda: ["FAILED"])

class StepConfig(BaseModel):
    name: str
    type: str = "INSTRUCTION"  # INSTRUCTION, TOOL_USE
    instruction: Optional[str] = None
    tool_name: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    
class AgentConfig(BaseModel):
    name: str
    model: str
    steps: List[StepConfig]
    tools: List[str] = Field(default_factory=list)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    
class AgentDefinition(BaseModel):
    id: str
    name: str
    version: str
    config: AgentConfig
    model: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
