import os
import re
from typing import List, Optional

class MigrationManager:
    """
    Manages versioned SQL migrations for the Cortex Runtime.
    """
    def __init__(self, migration_dir: str = None):
        from cortex_runtime.db.client import DBClient
        from cortex_runtime.db.state import StateManager
        
        self.db_client = DBClient()
        self.session = self.db_client.connect()
        
        # Default to 'migrations/sql' relative to this file
        if not migration_dir:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.migration_dir = os.path.join(base_dir, "sql")
        else:
            self.migration_dir = migration_dir

    def ensure_history_table(self):
        """Creates the SCHEMA_MIGRATIONS table if it doesn't exist."""
        if not self.session:
             print("[Migrations] Mock mode: stored in memory only.")
             return

        # Basic table to track applied migrations
        sql = """
        CREATE TABLE IF NOT EXISTS CORTEX_AGENT_RUNTIME.CORE.SCHEMA_MIGRATIONS (
            version STRING PRIMARY KEY,
            filename STRING,
            applied_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        );
        """
        try:
            self.session.sql(sql).collect()
        except Exception as e:
            print(f"[Migrations] Warning creating history table: {e}")

    def get_applied_versions(self) -> List[str]:
        if not self.session:
            return []
            
        try:
            res = self.session.sql("SELECT version FROM CORTEX_AGENT_RUNTIME.CORE.SCHEMA_MIGRATIONS").collect()
            return [row['VERSION'] for row in res]
        except Exception:
            return []

    def load_migration_files(self) -> List[dict]:
        """Reads SQL files and sorts them by version number prefix."""
        files = []
        if not os.path.exists(self.migration_dir):
            print(f"[Migrations] Directory not found: {self.migration_dir}")
            return []
            
        for f in os.listdir(self.migration_dir):
            if f.endswith(".sql"):
                # Extract version from filename "001_desc.sql" -> "001"
                match = re.match(r"^(\d+)_", f)
                if match:
                    files.append({
                        "version": match.group(1),
                        "filename": f,
                        "path": os.path.join(self.migration_dir, f)
                    })
        
        # Sort by version
        return sorted(files, key=lambda x: x['version'])

    def apply_migrations(self):
        print(f"[Migrations] Checking for updates in {self.migration_dir}...")
        
        if not self.session:
            print("[Migrations] Mock Mode: Skipping actual SQL execution.")
        
        self.ensure_history_table()
        applied = self.get_applied_versions()
        files = self.load_migration_files()
        
        count = 0
        for m in files:
            if m['version'] not in applied:
                print(f"[Migrations] Applying {m['filename']}...")
                self._run_file(m['path'])
                self._mark_applied(m)
                count += 1
        
        if count == 0:
            print("[Migrations] Database is up to date.")
        else:
            print(f"[Migrations] Successfully applied {count} migrations.")

    def _run_file(self, path):
        if not self.session: 
            return
            
        with open(path, 'r') as f:
            content = f.read()
            
        # Split by command if necessary, or run as one block if Snowflake supports it
        # Snowflake python worksheet/API usually allows one statement per call, 
        # so we split by semicolon carefully or assume the file is valid script.
        # Simple split for prototype:
        statements = [s.strip() for s in content.split(';') if s.strip()]
        for stmt in statements:
             self.session.sql(stmt).collect()

    def _mark_applied(self, migration):
        if not self.session:
            return
        
        sql = f"""
        INSERT INTO CORTEX_AGENT_RUNTIME.CORE.SCHEMA_MIGRATIONS (version, filename)
        VALUES ('{migration['version']}', '{migration['filename']}')
        """
        self.session.sql(sql).collect()
