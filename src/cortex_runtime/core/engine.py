import time
from typing import Dict, Any
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import LLMProvider
from cortex_runtime.models.agent import AgentDefinition, AgentConfig

class ExecutionEngine:
    def __init__(self, state_manager: StateManager, provider: LLMProvider):
        self.state_manager = state_manager
        self.provider = provider

    def run_agent_loop(self):
        """Main polling loop"""
        print("[Runtime] Starting agent polling loop...")
        while True:
            # 1. Poll for pending runs
            pending_runs = self.state_manager.fetch_pending_runs()
            
            # For demo purposes, if no DB connection and no pending runs, wait
            if not pending_runs:
                 if not self.state_manager.session:
                     # In mock mode, we might just be waiting for a test script to inject a run
                     time.sleep(1) 
                 else:
                     time.sleep(2)
                 continue
                 
            for run_row in pending_runs:
                self.execute_run(run_row)
                
            time.sleep(1)

    def execute_run(self, run_row: Dict):
        """Execute a single agent run"""
        run_id = run_row['run_id']
        agent_name = run_row['agent_name']
        
        self.state_manager.update_run_status(run_id, 'RUNNING')
        
        # 2. Load Definition
        # In mock mode, we try to fetch, if None, we assume it's attached to the run_row for testing
        # or we error out.
        defn_yaml = self.state_manager.fetch_agent_definition(agent_name)
        
        agent_config = None
        if not defn_yaml and 'mock_config' in run_row:
             agent_config = run_row['mock_config'] # Expecting an AgentConfig object
        elif defn_yaml:
             # Parse yaml... (Skipping parsing logic for prototype simplicity, assume pre-parsed object)
             pass 
             
        if not agent_config:
             print(f"[Runtime] Error: No definition found for {agent_name}")
             self.state_manager.update_run_status(run_id, 'FAILED')
             return

        print(f"[Runtime] Executing Run {run_id} for Agent {agent_name}")
        
        # 3. Resume / Start
        current_step_index = run_row.get('current_step_index', 0)
        
        # 4. Execute Steps
        steps = agent_config.steps
        context = {"input": run_row.get('input', {})}
        
        try:
            for i in range(current_step_index, len(steps)):
                step = steps[i]
                print(f"[Runtime] --> Executing Step {i}: {step.name} ({step.type})")
                
                step_result = self.run_single_step(step, context, agent_config.model)
                
                # Log step
                self.state_manager.log_step(run_id, {
                    "step_name": step.name,
                    "status": "SUCCESS",
                    "output": step_result,
                    "latency_ms": 100 # Mock
                })
                
                # Update context
                context[step.name] = step_result
                
            self.state_manager.update_run_status(run_id, 'COMPLETED')
            
        except Exception as e:
            print(f"[Runtime] Step failed: {e}")
            self.state_manager.update_run_status(run_id, 'FAILED')

    def run_single_step(self, step_config, context, model):
        """Execute a single step deterministically"""
        # Resolve inputs (simple Jinja-like replacement would go here)
        # For prototype, we just pass the instruction
        
        if step_config.type == "INSTRUCTION":
            result = self.provider.generate(
                prompt=step_config.instruction,
                model=model,
                config={}
            )
            return result.text
            
        elif step_config.type == "TOOL_USE":
            # Mock tool execution
            return {"tool_output": f"Mock result for {step_config.tool_name}"}
            
        return None
