# Basic Agent Example

This example demonstrates how to define, register, and run a basic Cortex Agent using the Runtime.

## Prerequisites

- Python 3.9+
- A Snowflake account (Standard, Enterprise, or Business Critical) if running in real mode.
- `snowsql` CLI (optional, for setting up tables)

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you are running from the source repo, ensure the package is installed or `PYTHONPATH` includes `src`.*

2. **Setup Snowflake Tables**
   Execute the setup script in your Snowflake account:
   ```bash
   snowsql -f setup_schema.sql -D database=YOUR_DB -s schema=YOUR_SCHEMA
   ```

3. **Configure Connection**
   Set the following environment variables to connect to your Snowflake instance:
   ```bash
   export SNOWFLAKE_ACCOUNT="<your_account>"
   export SNOWFLAKE_USER="<your_user>"
   export SNOWFLAKE_PASSWORD="<your_password>"
   export SNOWFLAKE_WAREHOUSE="<your_warehouse>"
   export SNOWFLAKE_DATABASE="<your_database>"
   export SNOWFLAKE_SCHEMA="<your_schema>"
   ```
   
   *If these are not set, the script accepts a fallback to MOCK mode which simulates the execution without a DB.*

## Running the Example

Run the python script:

```bash
python run.py
```

### What happens?

1. The script connects to Snowflake using the provided credentials.
2. It reads `agent.yaml` and upserts the definition into the `AGENT_DEFINITIONS` table.
3. It creates a new unique `run_id` and inserts a run request into the `AGENT_RUNS` table with status 'PENDING'.
4. It starts the Runtime Engine, which polls for the pending run.
5. The Engine picks up the run, fetches the definition, and executes the steps defined in YAML.
6. Execution logs and results are printed to the console and updated in the DB.

## Customization

Modify `agent.yaml` to change the prompt or add more steps.
