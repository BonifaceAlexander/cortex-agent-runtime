import sys
import os
from cortex_runtime.db.client import DBClient
from cortex_runtime.db.state import StateManager
from cortex_runtime.core.adapter import get_llm_provider
from cortex_runtime.core.engine import ExecutionEngine

def main():
    print("="*60)
    print("   Cortex Agent Runtime - Snowflake Control Plane")
    print("="*60)
    
    # 1. Initialize Snowflake Connection
    # In prod, credentials would be loaded from env or key-pair
    db_client = DBClient()
    session = db_client.connect()
    
    if session:
        print("[Init] Connected to Snowflake.")
    else:
        print("[Init] Running in MOCK mode (No Snowflake connection).")

    # 2. Components
    state_manager = StateManager(session)
    provider = get_llm_provider("cortex", session)
    
    # 3. Start Engine
    engine = ExecutionEngine(state_manager, provider)
    
    try:
        engine.run_agent_loop()
    except KeyboardInterrupt:
        print("\n[Runtime] Shutting down.")

if __name__ == "__main__":
    main()
