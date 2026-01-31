import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# --- MOCK DEPENDENCIES BEFORE IMPORT ---
# This is necessary because the CI/Agent environment might not have snowflake installed
# and we want to verify the logic flow.

mock_snowflake = MagicMock()
sys.modules['snowflake'] = mock_snowflake

mock_snowpark = MagicMock()
sys.modules['snowflake.snowpark'] = mock_snowpark

mock_connector = MagicMock()
sys.modules['snowflake.connector'] = mock_connector

# Mocks for DBClient etc will be handled via patching or reliance on these sys modules
# ---------------------------------------

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Also ensure examples/basic_agent is importable to run main
sys.path.append(str(Path(__file__).parent.parent / "examples" / "basic_agent"))

# Now we can import run.py, but we need to make sure it doesn't fail import
# Since we mocked snowflake, importing cortex_runtime (which imports snowflake) should work.
import run 

def test_basic_agent_run_mock_mode(capsys):
    """
    Test that the basic agent example runs in mock mode without error.
    """
    # We patch DBClient.connect to return None, forcing Mock mode logic in run.py
    # NOTE: DBClient import in run.py is already bound to the module `run` imports
    # so we should patch where it is used.
    
    with patch('cortex_runtime.db.client.DBClient.connect', return_value=None):
        # Patch sleep to speed up test
        with patch('time.sleep', return_value=None): 
            try:
                run.main()
            except SystemExit:
                pass
            except Exception as e:
                # If execution engine fails because of some other dependency, print it
                import traceback
                traceback.print_exc()
                raise e

    # Capture output
    captured = capsys.readouterr()
    
    # Assertions
    # We expect the header
    assert "Cortex Agent Runtime: Basic Agent Example" in captured.out
    
    # We expect fallback to mock mode because we forced connect() -> None
    assert "Running in MOCK mode" in captured.out
    
    # We expect confirmation of execution
    assert "Starting Engine Loop" in captured.out
    # In mock mode, run.py (as written) creates a mock run and executes it
    assert "Run" in captured.out and "executed" in captured.out
