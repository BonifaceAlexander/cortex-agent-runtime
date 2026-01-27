from typing import Optional, Dict, List
from datetime import datetime
import json

class StateManager:
    def __init__(self, session):
        self.session = session

    def fetch_agent_definition(self, agent_name: str) -> Optional[Dict]:
        """Fetch the latest active agent definition"""
        if not self.session:
            return None # Mock fallback
            
        # SQL: SELECT definition_yaml FROM AGENT_DEFINITIONS WHERE agent_name = ? AND status = 'active'
        return {}

    def fetch_pending_runs(self) -> List[Dict]:
        """Poll for PENDING runs"""
        # SQL: SELECT * FROM AGENT_RUNS WHERE status = 'PENDING'
        return []

    def log_step(self, run_id: str, step_data: Dict):
        """Write a step result to AGENT_STEPS"""
        # INSERT INTO AGENT_STEPS ...
        print(f"[DB] Logging step for run {run_id}: {step_data.get('step_name')}")

    def update_run_status(self, run_id: str, status: str, cost: float = 0.0):
        """Update AGENT_RUNS status"""
        print(f"[DB] Updating run {run_id} status to {status}")

    def save_memory(self, run_id: str, key: str, value: Any):
        """Save to AGENT_MEMORY"""
        pass
