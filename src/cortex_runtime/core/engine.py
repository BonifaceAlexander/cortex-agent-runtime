import os
import time
import signal
import sys
from typing import Dict, Any, Set, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, Future
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import LLMProvider
from cortex_runtime.models.agent import AgentDefinition, AgentConfig
from cortex_runtime.tools.registry import ToolRegistry

class ExecutionEngine:
    def __init__(self, state_manager: StateManager, provider: LLMProvider, max_workers: int = 10, tools: Optional[Dict[str, Callable]] = None):
        self.state_manager = state_manager
        self.provider = provider
        
        # Env var override for workers
        env_workers = os.getenv('CR_MAX_WORKERS')
        if env_workers:
            max_workers = int(env_workers)
            
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running = True
        self._active_futures: Set[Future] = set()
        
        # Tool Registry
        self.tool_registry = ToolRegistry()
        if tools:
            for name, func in tools.items():
                self.tool_registry.register(name, func)

        
        # Signal handling
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)

    def _shutdown_handler(self, signum, frame):
        print("\n[Runtime] Shutdown signal received. Stopping loop...")
        self._running = False

    def run_agent_loop(self):
        """Main polling loop with parallel execution and graceful shutdown"""
        print("[Runtime] Starting high-scale agent polling loop... (Ctrl+C to stop)")
        while self._running:
            # 1. Clean up finished futures
            done_futures = {f for f in self._active_futures if f.done()}
            for f in done_futures:
                try:
                    f.result() # check for exceptions
                except Exception as e:
                    print(f"[Runtime] Error in worker thread: {e}")
            self._active_futures -= done_futures

            # 2. Poll for pending runs (Batch)
            pending_runs = self.state_manager.fetch_pending_runs(limit=10)
            
            # For demo purposes, if no DB connection and no pending runs, wait
            if not pending_runs:
                 if not self.state_manager.session:
                     time.sleep(1) 
                 else:
                     time.sleep(2)
                 continue
                 
            # 3. Submit batch to executor
            for run_row in pending_runs:
                if not self._running:
                    break
                future = self.executor.submit(self.execute_run, run_row)
                self._active_futures.add(future)
                
            time.sleep(1)
            
        print("[Runtime] Loop stopped. Waiting for active workers to finish...")
        self.executor.shutdown(wait=True)
        print("[Runtime] Shutdown complete. Goodbye.")

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
        # The fetch query now returns 'completed_steps' count
        # If resuming, we start from that index.
        current_step_index = run_row.get('completed_steps', 0)
        
        # 4. Execute Steps
        steps = agent_config.steps
        
        # Initialize context with input AND spread input fields for direct access
        run_input = run_row.get('input', {})
        context = {"input": run_input}
        if isinstance(run_input, dict):
             context.update(run_input)
        
        try:
            for i in range(current_step_index, len(steps)):
                step = steps[i]
                print(f"[Runtime] --> Executing Step {i}: {step.name} ({step.type})")
                
                # result is now an LLMResult object or dict with metrics
                result_obj = self.run_single_step(step, context, agent_config.model)
                
                # Extract text for context linkage
                output_text = result_obj.text if hasattr(result_obj, 'text') else result_obj.get('tool_output', '')
                
                # Metrics
                tokens = result_obj.tokens_used if hasattr(result_obj, 'tokens_used') else 0
                latency = result_obj.latency_ms if hasattr(result_obj, 'latency_ms') else 0
                
                # Log step with full fidelity
                self.state_manager.log_step(run_id, {
                    "step_index": i,
                    "step_name": step.name,
                    "status": "SUCCESS",
                    "output": output_text,
                    "model": agent_config.model,
                    "tokens_used": tokens,
                    "latency_ms": latency
                })
                
                # Update context
                context[step.name] = output_text
                
            self.state_manager.update_run_status(run_id, 'COMPLETED')
            
        except Exception as e:
            print(f"[Runtime] Step failed: {e}")
            self.state_manager.update_run_status(run_id, 'FAILED')

    def run_single_step(self, step_config, context, model):
        """Execute a single step deterministically"""
        # Resolve inputs (simple Jinja-like replacement would go here)
        
        if step_config.type == "INSTRUCTION":
            # Return the full LLMResult object
            return self.provider.generate(
                prompt=step_config.instruction,
                model=model,
                config={}
            )
            
        elif step_config.type == "TOOL_USE":
            # Dynamic Tool Execution
            start_time = time.time()
            try:
                # Assuming input is relevant part of context or step_config, 
                # for prototype we assume the step has a 'tool_input' or we pass full context
                # Ideally step_config has 'tool_input' map.
                # Here we pass full context for simplicity + flexibility
                output = self.tool_registry.execute(step_config.tool_name, context)
                
                latency = (time.time() - start_time) * 1000
                return {
                    "tool_output": str(output), # conversion to string for safety
                    "tokens_used": 0, 
                    "latency_ms": latency
                }
            except Exception as e:
                return {
                    "tool_output": f"Error executing tool {step_config.tool_name}: {e}",
                    "tokens_used": 0,
                    "latency_ms": (time.time() - start_time) * 1000
                }
            
        return None

    def resume_run(self, run_id: str):
        """
        Resume a FAILED or STOPPED run from the last successful step.
        This enables deterministic replay and failure recovery.
        """
        print(f"[Runtime] Resuming Run {run_id}...")
        
        # 1. Fetch run details
        # In a real implementation, we'd query AGENT_RUNS for the run_row
        pending = self.state_manager.fetch_pending_runs()
        # For prototype simplicity, we just look in pending or assume it's there
        # but technically a failed run isn't PENDING.
        # We would need fetch_run(run_id) on StateManager.
        
        # Simulating recovery by just setting it back to PENDING if we can find it
        if not self.state_manager.session:
            if run_id in self.state_manager._mock_runs:
                 self.state_manager._mock_runs[run_id]['status'] = 'PENDING'
                 print(f"[Runtime] Run {run_id} status reset to PENDING for retry.")
        else:
             self.state_manager.update_run_status(run_id, 'PENDING')
             print(f"[Runtime] Run {run_id} status reset to PENDING in DB.")

    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Get observability summary for a run: steps, total cost, latency.
        """
        # This would optimally query AGENT_RUNS and AGENT_STEPS
        return {
            "run_id": run_id,
            "status": "Check DB", # simplified
            "total_tokens": 0,    # would sum from steps
            "total_latency_ms": 0 # would sum from steps
        }
