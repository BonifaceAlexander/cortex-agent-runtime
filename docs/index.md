# Cortex Agent Runtime

**Cortex Agent Runtime** is a lightweight, Python-based runtime for orchestrating AI agents within the Snowflake Data Cloud. It provides a control plane for defining, executing, and monitoring agents directly where your data lives.

## Key Features

- **Snowflake Native**: Agents run and persist state directly in Snowflake tables.
- **High-Scale Engine**: Parallel execution worker pool handling multiple agents concurrently.
- **Disaster Recovery**: Resume interrupted runs deterministically from the last successful step.
- **Dynamic Tooling**: Registry-based execution of real Python tools, not just mocks.
- **Configurable**: Environment-based tuning for worker pools (`CR_MAX_WORKERS`) and batch sizes (`CR_FETCH_LIMIT`).
- **SQL-Based Management**: Define and monitor agents using simple SQL tables.
- **Extensible**: Protocol-based support for Cortex and Mock providers.

## Getting Started

Ready to jump in? Check out the [Getting Started](getting-started.md) guide.

## How it Works

1. **Define**: Create an `agent.yaml` definition.
2. **Register**: Upsert the definition to the `AGENT_DEFINITIONS` table.
3. **Run**: Insert a run request into `AGENT_RUNS`.
4. **Execute**: The Runtime polls for pending runs and executes the defined steps.


```mermaid
graph TD
    User[User] -->|Upsert Definition| DB[(Snowflake DB)]
    User -->|Insert Run| DB
    
    subgraph "Cortex Runtime"
        Engine[Execution Engine] -->|Poll Pending Runs| DB
        Engine -->|Fetch Definition| DB
        Engine -->|Execute Steps| LLM[Cortex LLM]
        Engine -->|Log Steps/Updates| DB
    end
    
    LLM -->|Response| Engine
```
