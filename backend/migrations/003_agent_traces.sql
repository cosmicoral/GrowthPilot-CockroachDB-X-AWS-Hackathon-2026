-- 003_agent_traces.sql — agent execution tracing and observability (T20)

CREATE TABLE IF NOT EXISTS agent_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    agent_name STRING NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    duration_ms FLOAT NOT NULL,
    input JSONB NOT NULL DEFAULT '{}',
    output JSONB NOT NULL DEFAULT '{}',
    memories_retrieved JSONB NOT NULL DEFAULT '[]',
    success BOOL NOT NULL,
    error STRING,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    INDEX idx_traces_company_time (company_id, created_at DESC),
    INDEX idx_traces_agent (company_id, agent_name, created_at DESC)
);
