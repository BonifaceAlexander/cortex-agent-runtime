# Getting Started

This guide will help you set up the Cortex Agent Runtime and run your first agent.

## Prerequisites

- **Python 3.9+**
- **Snowflake Account**: You need access to a specific database and schema.
- **SnowSQL** (Optional): Useful for running setup scripts.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/cortex-agent-runtime.git
   cd cortex-agent-runtime
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Basic Agent Example

We have included a "Basic Agent" example in the `examples/` directory.

### 1. Setup Snowflake Environment

Run the SQL setup script to create the necessary tables (`AGENT_DEFINITIONS`, `AGENT_RUNS`, etc.).

```bash
cd examples/basic_agent
snowsql -f setup_schema.sql -D database=YOUR_DB -s schema=YOUR_SCHEMA
```

### 2. Configure Credentials

Export your Snowflake credentials as environment variables:

```bash
export SNOWFLAKE_ACCOUNT="<your_account>"
export SNOWFLAKE_USER="<your_user>"
export SNOWFLAKE_PASSWORD="<your_password>"
export SNOWFLAKE_WAREHOUSE="<your_warehouse>"
export SNOWFLAKE_DATABASE="<your_database>"
export SNOWFLAKE_SCHEMA="<your_schema>"
```

### 3. Run the Agent

Execute the Python script:

```bash
python run.py
```

You should see logs indicating that the agent connected to Snowflake, registered itself, and executed the steps defined in `agent.yaml`.

## 4. Advanced Configuration (Optional)

You can tune the runtime performance using environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `CR_MAX_WORKERS` | `10` | Number of parallel threads for executing agents. |
| `CR_FETCH_LIMIT` | `10` | Number of jobs to fetch per polling cycle. |

```bash
export CR_MAX_WORKERS=50
export CR_FETCH_LIMIT=50
python run.py
```

## Next Steps

- Explore the [Architecture](architecture.md) to understand how it works under the hood.
- Check the [Database Schema](schema.md) reference.
- Try creating your own agent by modifying `agent.yaml`.
