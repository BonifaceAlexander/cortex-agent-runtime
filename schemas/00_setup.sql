-- 00_setup.sql
-- Run this to initialize the database environment

CREATE DATABASE IF NOT EXISTS CORTEX_AGENT_RUNTIME;
CREATE SCHEMA IF NOT EXISTS CORTEX_AGENT_RUNTIME.CORE;

USE SCHEMA CORTEX_AGENT_RUNTIME.CORE;

-- 1. AGENT_DEFINITIONS
-- Defines what an agent is. Config-first, versioned, auditable.
CREATE TABLE IF NOT EXISTS AGENT_DEFINITIONS (
  agent_id STRING NOT NULL PRIMARY KEY,
  agent_name STRING NOT NULL,
  version STRING NOT NULL,
  definition_yaml VARIANT,     -- The full config
  model STRING,                -- Cortex model reference
  retry_policy VARIANT,
  status STRING,               -- active / deprecated
  created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 2. AGENT_RUNS
-- One row per execution. Tracks cost, latency, and status.
CREATE TABLE IF NOT EXISTS AGENT_RUNS (
  run_id STRING NOT NULL PRIMARY KEY,
  agent_id STRING NOT NULL,
  agent_version STRING,
  status STRING,               -- PENDING / RUNNING / COMPLETED / FAILED
  triggered_by STRING,         -- user / api / schedule
  total_tokens NUMBER DEFAULT 0,
  total_cost NUMBER(10, 4) DEFAULT 0,
  error_message STRING,
  start_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  end_time TIMESTAMP_NTZ
);

-- 3. AGENT_STEPS
-- Fine-grained execution trace for debugging and forensics.
CREATE TABLE IF NOT EXISTS AGENT_STEPS (
  step_id STRING NOT NULL PRIMARY KEY,
  run_id STRING NOT NULL,
  step_index INTEGER,
  step_name STRING,
  step_type STRING,            -- INSTRUCTION / TOOL_USE
  input VARIANT,
  output VARIANT,
  model STRING,
  tokens_used NUMBER DEFAULT 0,
  latency_ms NUMBER DEFAULT 0,
  status STRING,               -- SUCCESS / FAILED
  error_message STRING,
  executed_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  FOREIGN KEY (run_id) REFERENCES AGENT_RUNS(run_id)
);

-- 4. AGENT_MEMORY
-- Persistent, queryable memory for time travel and audits.
CREATE TABLE IF NOT EXISTS AGENT_MEMORY (
  memory_id STRING NOT NULL PRIMARY KEY,
  run_id STRING NOT NULL,
  agent_id STRING,
  memory_type STRING,          -- CONVERSATION / TOOL / SCRATCHPAD
  key STRING,                  -- Optional key for Key-Value retrieval
  content VARIANT,
  created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  FOREIGN KEY (run_id) REFERENCES AGENT_RUNS(run_id)
);
