-- Setup Schema for Cortex Agent Runtime

CREATE OR REPLACE TABLE agent_definitions (
    agent_name VARCHAR(255) PRIMARY KEY,
    definition_yaml VARCHAR, -- Storing YAML as text for simplicity
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE agent_runs (
    run_id VARCHAR(36) PRIMARY KEY, -- UUID
    agent_name VARCHAR(255),
    input VARIANT,
    status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, FAILED
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE agent_steps (
    step_id VARCHAR(36) DEFAULT UUID_STRING(),
    run_id VARCHAR(36),
    step_index INT,           -- Added for Resume logic (0-indexed)
    step_name VARCHAR(255),
    status VARCHAR(50),
    output VARIANT,
    model VARCHAR(255),       -- Added for Telemetry
    tokens_used INT,          -- Added for Telemetry
    latency_ms INT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
