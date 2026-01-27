# System Design & Architecture

## The Core Mental Model

> **“The runtime treats Snowflake as the control plane, Cortex as the inference engine, and the execution layer as a stateless orchestrator.”**

### 🧠 Snowflake = Control Plane + State
Snowflake is the **System of Record**.
- **Agent Definitions**: Agents are declared as data, not code.
- **Agent Memory**: Conversation history, tool outputs, reasoning traces.
- **Observability**: Logs, metrics, costs.

### ⚙️ Runtime = Execution Engine (External)
The runtime is an external service/process that:
1.  **Reads** agent definitions from Snowflake.
2.  **Executes** steps deterministically using the Cortex Adapter.
3.  **Writes** results back to Snowflake (runs, steps, memory).

---

## 1️⃣ Snowflake Schema Design
Everything important is data, queryable with SQL.

### 🔹 AGENT_DEFINITIONS
Defines what an agent is. Config-first, versioned, auditable.
```sql
CREATE TABLE AGENT_DEFINITIONS (
  agent_id STRING,
  agent_name STRING,
  version STRING,
  definition_yaml VARIANT,     -- The full config
  model STRING,                -- Cortex model reference
  retry_policy VARIANT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  status STRING                -- active / deprecated
);
```

### 🔹 AGENT_RUNS
One row per execution. Tracks cost, latency, and status.
```sql
CREATE TABLE AGENT_RUNS (
  run_id STRING,
  agent_id STRING,
  agent_version STRING,
  status STRING,               -- running / failed / completed
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  triggered_by STRING,         -- user / api / schedule
  total_tokens NUMBER,
  total_cost NUMBER,
  error_message STRING
);
```

### 🔹 AGENT_STEPS
Fine-grained execution trace for debugging and forensics.
```sql
CREATE TABLE AGENT_STEPS (
  run_id STRING,
  step_index INTEGER,
  step_name STRING,
  input VARIANT,
  output VARIANT,
  model STRING,
  tokens_used NUMBER,
  latency_ms NUMBER,
  status STRING,
  error_message STRING,
  executed_at TIMESTAMP
);
```

### 🔹 AGENT_MEMORY
Persistent, queryable memory for time travel and audits.
```sql
CREATE TABLE AGENT_MEMORY (
  run_id STRING,
  agent_id STRING,
  memory_type STRING,          -- conversation / tool / scratchpad
  content VARIANT,
  created_at TIMESTAMP
);
```

### 🔹 AGENT_EVALUATIONS (Optional / v2)
Post-run scoring.
```sql
CREATE TABLE AGENT_EVALUATIONS (
  run_id STRING,
  metric_name STRING,
  metric_value FLOAT,
  evaluated_at TIMESTAMP
);
```

---

## 2️⃣ Architecture Flow

```mermaid
graph TD
    User[User / API / Schedule] -->|Trigger| Runtime[External Agent Runtime]
    Runtime -->|1. Load Definition| Defs[Snowflake: AGENT_DEFINITIONS]
    Runtime -->|2. Execute Step| Cortex[Snowflake Cortex (LLM)]
    Runtime -->|3. Persist State| State[Snowflake: RUNS / STEPS / MEMORY]
    State -->|4. Analytics| Analytics[Snowflake Analytics & Monitoring]
```

### 🧠 Separation of Concerns
| Component | Responsibility |
| :--- | :--- |
| **Snowflake** | State, memory, audit, governance, system of record |
| **Cortex** | Model inference (via Adapter) |
| **Runtime** | Execution, retries, orchestration, stateless logic |

---

## 3️⃣ Cortex Calls & Abstraction

### 🎯 Goal
We want **Cortex today**, other models tomorrow. No agent logic should be tied to a single model.

### 🧩 Cortex Adapter Pattern

**Interface (Conceptual)**
```python
class LLMProvider:
    def generate(self, prompt: str, config: dict) -> LLMResult:
        ...
```

**Cortex Implementation**
```python
class CortexProvider(LLMProvider):
    def generate(self, prompt: str, config: dict) -> LLMResult:
        # call SNOWFLAKE.CORTEX.COMPLETE(...)
        # standardized metrics logging
        return LLMResult(
            text="...",
            tokens=123,
            latency_ms=456
        )
```

### 🔐 Governance Advantage
- All calls go through a single adapter.
- Tokens, cost, and latency are logged centrally.
- Results are persisted to Snowflake.
- **Result**: Centralized control, easy cost guardrails, enterprise observability.

---

## 🚫 What We Are NOT Doing
- ❌ Running persistent agents inside Snowflake.
- ❌ Replacing Snowflake workflows.
- ❌ Executing uncontrolled Python loops in Snowflake.
- ❌ Turning Snowflake into an app server.
