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
        try:
            rows = self.session.sql(
                "SELECT definition_yaml FROM agent_definitions WHERE agent_name = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
                params=[agent_name]
            ).collect()
            
            if rows:
                import yaml
                return yaml.safe_load(rows[0]['DEFINITION_YAML'])
        except Exception as e:
            print(f"[DB] Error fetching definition: {e}")
            
        return None

    def fetch_pending_runs(self, limit: int = 10) -> List[Dict]:
        # Allow env override if default value is passed
        import os
        if limit == 10: # Only override default
             limit = int(os.getenv('CR_FETCH_LIMIT', 10))

        """
        Poll for PENDING runs with safer claiming logic.
        Strategy: UPDATE status='RUNNING' for next N rows, returning the modified rows if possible.
        Since Snowpark SELECT returning modified rows is tricky, we do:
        1. UPDATE top N pending -> RUNNING
        2. SELECT those we just updated (approximate match by time/status)
        
        *Note*: In a multi-worker cluster without unique 'claimed_by' ID, this has a small race condition
        where two workers might update overlapping sets. 
        For this 'hardened' version without schema changes, we rely on the fact that
        updating 'PENDING' -> 'RUNNING' is atomic per row, so double-execution is minimized.
        """
        if not self.session:
            # Return any mock runs that are 'PENDING', up to limit
            all_pending = [r for r in self._mock_runs.values() if r['status'] == 'PENDING']
            batch = all_pending[:limit]
            # Mock the state transition immediately to simulate claiming
            for r in batch:
                r['status'] = 'RUNNING' 
            return batch

        try:
            # 1. Atomic UPDATE first (The "Claim")
            # We target the oldest PENDING rows. 
            # Note: This is an "optimistic claim".
            self.session.sql(
                f"""
                UPDATE agent_runs 
                SET status = 'RUNNING', updated_at = CURRENT_TIMESTAMP()
                WHERE run_id IN (
                    SELECT run_id FROM agent_runs 
                    WHERE status = 'PENDING' 
                    ORDER BY created_at ASC 
                    LIMIT {limit}
                )
                """
            ).collect()
            
            # 2. SELECT what we (likely) just claimed
            # We fetch 'RUNNING' jobs that were updated very recently.
            rows = self.session.sql(
                f"""
                SELECT r.run_id, r.agent_name, r.input, r.status, COUNT(s.step_id) as completed_steps
                FROM agent_runs r
                LEFT JOIN agent_steps s ON r.run_id = s.run_id AND s.status = 'SUCCESS'
                WHERE r.status = 'RUNNING' 
                AND r.updated_at >= TIMEADD('second', -5, CURRENT_TIMESTAMP())
                GROUP BY r.run_id, r.agent_name, r.input, r.status
                LIMIT {limit}
                """
            ).collect()
            
            runs = []
            for row in rows:
                runs.append({
                    'run_id': row['RUN_ID'],
                    'agent_name': row['AGENT_NAME'],
                    'input': json.loads(row['INPUT']) if row['INPUT'] else {},
                    'status': row['STATUS'],
                    'completed_steps': row['COMPLETED_STEPS'] if row['COMPLETED_STEPS'] else 0
                })
            return runs
        except Exception as e:
            print(f"[DB] Error fetching runs: {e}")
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

        # INSERT INTO AGENT_STEPS
        try:
             import json
             self.session.sql(
                 """INSERT INTO agent_steps (run_id, step_index, step_name, status, output, model, tokens_used, latency_ms) 
                    VALUES (?, ?, ?, ?, parse_json(?), ?, ?, ?)""",
                 params=[
                     run_id, 
                     step_data.get('step_index', 0),
                     step_data.get('step_name'), 
                     step_data.get('status'), 
                     json.dumps(step_data.get('output')), 
                     step_data.get('model', 'unknown'),
                     step_data.get('tokens_used', 0),
                     step_data.get('latency_ms', 0)
                 ]
             ).collect()
             print(f"[DB] Logging step for run {run_id}: {step_data.get('step_name')}")
        except Exception as e:
            print(f"[DB] Error logging step: {e}")

    def update_run_status(self, run_id: str, status: str, cost: float = 0.0):
        """Update AGENT_RUNS status"""
        if not self.session:
            if run_id in self._mock_runs:
                self._mock_runs[run_id]['status'] = status
                print(f"[MockDB] Run {run_id} status updated to {status}")
            return
            
        print(f"[DB] Updating run {run_id} status to {status}")
        try:
            self.session.sql(
                "UPDATE agent_runs SET status = ?, updated_at = CURRENT_TIMESTAMP() WHERE run_id = ?",
                params=[status, run_id]
            ).collect()
        except Exception as e:
            print(f"[DB] Error updating run status: {e}")

    def save_memory(self, run_id: str, key: str, value: Any):
        """Save to AGENT_MEMORY"""
        if not self.session:
             self._mock_memory[(run_id, key)] = value
             print(f"[MockDB] Memory saved: {key}")
             return
        pass
