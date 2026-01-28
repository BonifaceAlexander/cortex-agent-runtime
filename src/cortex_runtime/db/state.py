from typing import Optional, Dict, List, Any
from datetime import datetime
import json

class StateManager:
    def __init__(self, session):
        self.session = session
        # Mock storage for prototype
        self._mock_runs = {}
        self._mock_steps = []
        self._mock_memory = {}

    def fetch_agent_definition(self, agent_name: str) -> Optional[Dict]:
        """Fetch the latest active agent definition"""
        if not self.session:
            # In mock mode, we expect the definitions to be pre-loaded or passed
            # For simplicity, we return None and let the Engine handle config loading separately
            # or we could stick a mock definition here.
            return None
            
        # SQL: SELECT definition_yaml FROM AGENT_DEFINITIONS WHERE agent_name = ? AND status = 'active'
        return {}

    def fetch_pending_runs(self) -> List[Dict]:
        """Poll for PENDING runs"""
        if not self.session:
            # Return any mock runs that are 'PENDING'
            return [r for r in self._mock_runs.values() if r['status'] == 'PENDING']

        # SQL: SELECT * FROM AGENT_RUNS WHERE status = 'PENDING'
        return []

    def mock_add_run(self, run_dict: Dict):
        """Helper to inject a run for testing"""
        self._mock_runs[run_dict['run_id']] = run_dict

    def log_step(self, run_id: str, step_data: Dict):
        """Write a step result to AGENT_STEPS"""
        if not self.session:
            self._mock_steps.append(step_data)
            print(f"[MockDB] Run {run_id} | Step {step_data.get('step_name')} | Status: {step_data.get('status')}")
            return

        # INSERT INTO AGENT_STEPS ...
        print(f"[DB] Logging step for run {run_id}: {step_data.get('step_name')}")

    def update_run_status(self, run_id: str, status: str, cost: float = 0.0):
        """Update AGENT_RUNS status"""
        if not self.session:
            if run_id in self._mock_runs:
                self._mock_runs[run_id]['status'] = status
                print(f"[MockDB] Run {run_id} status updated to {status}")
            return
            
        print(f"[DB] Updating run {run_id} status to {status}")

    def save_memory(self, run_id: str, key: str, value: Any):
        """Save to AGENT_MEMORY"""
        if not self.session:
             self._mock_memory[(run_id, key)] = value
             print(f"[MockDB] Memory saved: {key}")
             return
        pass
