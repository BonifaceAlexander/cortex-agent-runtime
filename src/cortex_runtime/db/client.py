from snowflake.snowpark import Session
import os

class DBClient:
    def __init__(self, connection_params=None):
        self.session = None
        self._connection_params = connection_params

    def connect(self):
        if self.session:
            return self.session
            
        # If no params provided, try to create from environment or default config
        if not self._connection_params:
            # For local dev without real snowflake, we might mocking this
            # In production, use standard connection builder
            try:
                self.session = Session.builder.configs(os.environ).create()
            except Exception as e:
                print(f"Warning: Could not connect to Snowflake: {e}")
                self.session = None # Proceed in mock mode if needed
        else:
             self.session = Session.builder.configs(self._connection_params).create()
             
        return self.session

    def get_session(self):
        return self.session
