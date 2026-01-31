import os
import sys
import json
import uuid
import yaml
from pathlib import Path

# Add src to path so we can import cortex_runtime
# In a real install, cortex_runtime would be in site-packages
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from cortex_runtime.db.client import DBClient
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import get_llm_provider
from cortex_runtime.core.engine import ExecutionEngine

def main():
    print("=== Cortex Agent Runtime: Basic Agent Example ===")
    
    # 1. Connect to Snowflake
    # Make sure you have SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ACCOUNT, etc. set in env
    # or rely on default config
    print("[1] Connecting to Snowflake...")
    db_client = DBClient()
    session = db_client.connect()
    
    if not session:
        print("⚠️  Could not connect to Snowflake. Running in MOCK mode.")
        print("   (Set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA to run for real)")
    else:
        print("✅  Connected to Snowflake.")

    state_manager = StateManager(session)
    
    # 2. Register Agent Definition
    agent_yaml_path = Path(__file__).parent / "agent.yaml"
    print(f"[2] Reading agent definition from {agent_yaml_path}")
    with open(agent_yaml_path, "r") as f:
        agent_def_str = f.read()
        agent_def = yaml.safe_load(agent_def_str)
        
    agent_name = agent_def['name']
    
    if session:
        print(f"[2.1] Upserting agent '{agent_name}' to AGENT_DEFINITIONS table...")
        try:
            # Simple upsert logic
            session.sql(
                 """MERGE INTO agent_definitions AS target
                    USING (SELECT ? AS agent_name, ? AS definition_yaml, 'active' AS status) AS source
                    ON target.agent_name = source.agent_name
                    WHEN MATCHED THEN UPDATE SET target.definition_yaml = source.definition_yaml, target.created_at = CURRENT_TIMESTAMP()
                    WHEN NOT MATCHED THEN INSERT (agent_name, definition_yaml, status) VALUES (source.agent_name, source.definition_yaml, source.status)""",
                 params=[agent_name, agent_def_str]
            ).collect()
        except Exception as e:
            print(f"❌ Error upserting agent definition: {e}")
            return
    else:
        # Mock mode registration (not fully implemented in StateManager mock but we can skip)
        pass

    # 3. Create a Run
    run_id = str(uuid.uuid4())
    print(f"[3] Creating new run {run_id} for agent '{agent_name}'...")
    
    run_input = {"user_message": "Hello!"}
    
    if session:
        try:
            session.sql(
                """INSERT INTO agent_runs (run_id, agent_name, input, status) 
                   VALUES (?, ?, parse_json(?), 'PENDING')""",
                params=[run_id, agent_name, json.dumps(run_input)]
            ).collect()
        except Exception as e:
            print(f"❌ Error creating run: {e}")
            return
    else:
        state_manager.mock_add_run({
            'run_id': run_id,
            'agent_name': agent_name,
            'input': run_input,
            'status': 'PENDING'
        })
        # Inject config for mock mode since StateManager mock doesn't store definitions
        # This implementation detail depends on how engine.py handles mocks
        # But engine.py line 46 checks 'mock_config' in run_row
        from cortex_runtime.models.agent import AgentConfig, StepConfig
        # Construct mock config object manually for the test/mock path
        steps = [StepConfig(**s) for s in agent_def['steps']]
        mock_config = AgentConfig(name=agent_name, model=agent_def['model'], steps=steps)
        state_manager._mock_runs[run_id]['mock_config'] = mock_config

    # 4. Start Runtime
    print("[4] Starting Engine Loop to process runs...")
    print("    (Press Ctrl+C to stop once the agent finishes)")
    
    provider = get_llm_provider("cortex", session)
    engine = ExecutionEngine(state_manager, provider)
    
    try:
        # Loop until our specific run is complete (custom logic for this script)
        # We can't use engine.run_agent_loop() because it loops forever.
        # We'll mimic the loop but check for our run status.
        
        while True:
            # Poll pending
            pending = state_manager.fetch_pending_runs()
            my_run = next((r for r in pending if r['run_id'] == run_id), None)
            
            if my_run:
                engine.execute_run(my_run)
                print(f"✅  Run {run_id} executed.")
                break
            
            # Check if run is already completed (in case it was picked up fast or something)
            # This requires fetching status again, which StateManager doesn't expose easily without SQL.
            # But since we are the only runner, if it wasn't in pending, maybe it's done?
            # Or maybe we just rely on execute_run being synchronous in this prototype.
            
            # Since execute_run IS synchronous in the current engine.py:
            # We found it in pending -> executed it -> it's done. 
            # If we didn't find it in pending, wait?
            if not session and len(pending) == 0:
                 print("No pending runs found in mock mode ??")
                 break
            
            if session:
                # Check status in DB
                status_row = session.sql("SELECT status FROM agent_runs WHERE run_id = ?", params=[run_id]).collect()
                if status_row and status_row[0]['STATUS'] in ['COMPLETED', 'FAILED']:
                    print(f"Run finished with status: {status_row[0]['STATUS']}")
                    break
                    
            import time
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()
