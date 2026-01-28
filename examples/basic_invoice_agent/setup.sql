-- SQL Setup for Invoice Validator Agent

USE SCHEMA CORTEX_AGENT_RUNTIME.CORE;

-- Insert the Agent Definition
INSERT INTO AGENT_DEFINITIONS (agent_id, agent_name, version, status, model, definition_yaml)
SELECT 
    'inv_val_001', 
    'invoice_validator', 
    '1.0.0', 
    'ACTIVE', 
    'cortex.llama3',
    PARSE_JSON($$
      {
        "agent": {
            "name": "invoice_validator",
            "model": "cortex.llama3",
            "steps": [
                {"name": "extract_entities", "type": "INSTRUCTION", "instruction": "Extract vendor..."},
                {"name": "validate_math", "type": "TOOL_USE", "tool_name": "math_validator"},
                {"name": "generate_summary", "type": "INSTRUCTION", "instruction": "Generate JSON summary..."}
            ]
        }
      }
    $$);

-- Trigger a Run (Manual)
INSERT INTO AGENT_RUNS (run_id, agent_id, agent_version, status, triggered_by)
VALUES ('run_123', 'inv_val_001', '1.0.0', 'PENDING', 'user_manual');
