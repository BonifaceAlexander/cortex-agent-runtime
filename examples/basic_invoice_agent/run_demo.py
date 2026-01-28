import sys
import os
import yaml
import threading
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

from cortex_runtime.db.client import DBClient
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import get_llm_provider
from cortex_runtime.core.engine import ExecutionEngine
from cortex_runtime.models.agent import AgentConfig

def run_demo():
    print("🚀 Starting Cortex Agent Runtime - Prototype Demo")
    
    # 1. Initialize Mock Components
    db_client = DBClient() # No creds = Mock Mode
    session = db_client.connect()
    
    state_manager = StateManager(session)
    provider = get_llm_provider("cortex", session)
    engine = ExecutionEngine(state_manager, provider)
    
    # 2. Load Agent Config
    yaml_path = os.path.join(os.path.dirname(__file__), 'agent.yaml')
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        
    # Manually parse into Pydantic Model (simplifying for demo)
    # The keys in yaml need to match Pydantic fields
    agent_data = data['agent']
    config = AgentConfig(**agent_data)
    
    print(f"✅ Loaded Agent: {config.name}")
    
    # 3. Inject Mock Run
    run_id = "run_demo_001"
    state_manager.mock_add_run({
        "run_id": run_id,
        "agent_name": config.name,
        "status": "PENDING",
        "mock_config": config, # Injecting config directly for Engine to pick up
        "input": {"invoice_text": "Invoice #123 form Acme Corp. Total: $500. Date: 2023-10-01"}
    })
    
    print(f"✅ Injected Pending Run: {run_id}")
    
    # 4. Run Engine in Background Thread
    # We run it for 5 seconds then stop
    stop_event = threading.Event()
    
    def engine_runner():
        # A slightly modified loop that checks stop_event would be ideal, 
        # but for prototype we can just let it loop and daemon kill it, 
        # OR we just rely on engine.run_agent_loop being blocking and just run it for one cycle if we modified it.
        # Since engine.run_agent_loop is infinite, let's run it in a daemon thread.
        try:
             # We can't easily break the infinite loop in the current implementation without modifying Engine.
             # However, for this demo script, we can just let it run.
             engine.run_agent_loop()
        except:
             pass

    t = threading.Thread(target=engine_runner, daemon=True)
    t.start()
    
    # 5. Monitor Output
    print("\nProvoking Runtime Steps...")
    time.sleep(1) # Let engine pick up run
    
    # Poll Mock DB to see progress
    for _ in range(6):
        run = state_manager._mock_runs.get(run_id)
        print(f"[Monitor] Run Status: {run['status']}")
        
        if run['status'] == 'COMPLETED':
            print("\n🎉 Run Completed Successfully!")
            print("Captured Steps:")
            for s in state_manager._mock_steps:
                print(f" - {s['step_name']}: {s['output']}")
            break
        elif run['status'] == 'FAILED':
             print("❌ Run Failed.")
             break
             
        time.sleep(1)

    print("\nEnd of Demo.")

if __name__ == "__main__":
    run_demo()
