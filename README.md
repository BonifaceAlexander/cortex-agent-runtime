# Cortex Agent Runtime

[![Documentation](https://img.shields.io/badge/docs-live-blue.svg)](https://BonifaceAlexander.github.io/cortex-agent-runtime/)
[![Release](https://img.shields.io/github/v/release/BonifaceAlexander/cortex-agent-runtime)](https://github.com/BonifaceAlexander/cortex-agent-runtime/releases)

> **Full Documentation**: [https://BonifaceAlexander.github.io/cortex-agent-runtime/](https://BonifaceAlexander.github.io/cortex-agent-runtime/)

## Problem We Are Solving

### The real problem
**Snowflake provides powerful LLM capabilities (Cortex, MCP, Snowpark), but no production-grade execution runtime for AI agents.**

Today:
- Agent examples are stateless
- No persistent memory
- No failure recovery
- No deterministic replay
- No observability
- No governance trail

This makes it difficult for teams to:
- Run multi-step agents reliably
- Debug failures
- Track cost & performance
- Use agents in regulated or enterprise environments

**In short: Snowflake has models and data — but not a runtime to execute agents safely and repeatably.**

---

## 🛠️ How We Are Solving It

### Core idea
We introduce a **Snowflake-native agent execution runtime** where:
- State lives in Snowflake
- Execution is deterministic
- Failures are recoverable
- Every step is auditable

The runtime acts as a **control plane for agent execution** — not another agent framework.

### Key design choices (important for credibility)
- **Snowflake as the source of truth**
  - Agent state
  - Memory
  - Execution logs
  - Metrics
- **Config-first**
  - Agents defined via YAML
  - No hard-coded flows
- **Model-agnostic**
  - Cortex models today
  - Extendable tomorrow
- **Execution-focused**
  - Not prompt hacking
  - Not chaining APIs

---

## 🧱 What Exactly We Are Building

### 1️⃣ Agent Execution Runtime (Core)
- Step-by-step agent execution
- Deterministic state transitions
- Idempotent runs
- Replayable executions

**Think: “Airflow for AI agents — but Snowflake-native.”**

### 2️⃣ Snowflake-Backed Memory
- Conversation memory
- Tool outputs
- Intermediate reasoning state
- Stored in Snowflake tables

**Supports:**
- Time travel
- Audits
- Debugging
- Analytics on agent behavior

### 3️⃣ Reliability & Recovery
- Automatic retries
- Resume from last successful step
- Failure classification
- Partial execution recovery

*This is critical for enterprise trust.*

### 4️⃣ Observability & Cost Tracking
- Tokens per step
- Latency per step
- Cost per execution
- Error rates

*Stored and queryable in Snowflake.*

### 5️⃣ Config-Driven Agent Definition
Example (conceptual):
```yaml
agent:
  name: invoice_validator
  model: cortex.llama3
  steps:
    - extract_entities
    - validate_rules
    - generate_summary
  retry_policy:
    max_retries: 3
```

This makes the system:
- Auditable
- Reviewable
- Enterprise-friendly

### 6️⃣ High-Scale Distributed Execution
- **Concurrent Processing**: Execute 100+ agents in parallel using a worker pool.
- **Batch Polling**: Optimized DB queries for high throughput.
- **Microservice Ready**: Designed to run as a scalable service (ECS/K8s).

---

## 🚫 What We Are NOT Doing

*This section protects us from scope creep.*

### ❌ We are NOT building:
- Another RAG framework
- A LangChain wrapper
- A chatbot UI
- Prompt engineering templates
- Vector database tooling
- Model fine-tuning pipelines

### 3. Run the Engine
The runtime engine polls Snowflake for pending jobs and executes them.

First, install the package:
```bash
pip install -e .
```

Then run the engine using the CLI:
```bash
# Optional: Set concurrency limits
export CR_MAX_WORKERS=20
export CR_FETCH_LIMIT=20

cortex run
```

You can also manage database migrations:
```bash
cortex migrate
```
### ❌ We are NOT:
- Competing with Snowflake Cortex
- Replacing LangGraph or LangChain
- Building end-user applications
- Optimizing prompts for “clever” behavior

### ❌ We are NOT:
- A demo-only repository
- A research project
- A toy example
- A Snowflake-incompatible abstraction

---

## 🎯 What This Repo Is

**A production-grade execution runtime that makes Snowflake Cortex agents usable in real systems.**
